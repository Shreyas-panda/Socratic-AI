from typing import Dict, List, Any, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from database import TutorialDatabase

# Import the existing API configuration
from LLM_api import client
from rag_engine import RAGEngine

class TutorialState(TypedDict):
    """State object for the tutorial agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    subject: str
    conversation_id: int
    current_mode: str  # 'tutorial', 'qa', 'evaluation'
    evaluation_count: int
    user_understanding: Dict[str, Any]
    language: str
    retrieved_context: str # Added for RAG

class TutorialAgent:
    """LangGraph-based AI tutorial agent."""
    
    def __init__(self):
        self.db = TutorialDatabase()
        self.rag_engine = RAGEngine()
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(TutorialState)
        
        # Workflow is a type of graph builder that allows you to create a graph of nodes and edges.
        # Nodes are the states of the agent, and edges are the transitions between states.
        # Edges are the transitions between states. 
        
        # Add nodes
        workflow.add_node("generate_tutorial", self._generate_tutorial)
        workflow.add_node("retrieve_knowledge", self._retrieve_knowledge) # RAG Node
        workflow.add_node("handle_question", self._handle_question)
        workflow.add_node("create_evaluation", self._create_evaluation)
        workflow.add_node("evaluate_answer", self._evaluate_answer)
        
        # Set entry point
        workflow.set_entry_point("generate_tutorial")
        
        # Add conditional edges based on user input and current mode
        workflow.add_conditional_edges(
            "generate_tutorial",
            self._route_after_tutorial,
            {
                "question": "retrieve_knowledge", # Route to RAG first for questions
                "evaluation": "create_evaluation",
                "end": END
            }
        )
        
        # Edge from retrieval to question handling
        workflow.add_edge("retrieve_knowledge", "handle_question")
        
        workflow.add_conditional_edges(
            "handle_question",
            self._route_after_question,
            {
                "question": "retrieve_knowledge", # Loop back to RAG for follow-up questions
                "evaluation": "create_evaluation",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "create_evaluation",
            self._route_after_evaluation,
            {
                "question": "retrieve_knowledge",
                "evaluation": "create_evaluation",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "evaluate_answer",
            self._route_after_evaluation_answer,
            {
                "question": "retrieve_knowledge",
                "evaluation": "create_evaluation",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _generate_tutorial(self, state: TutorialState) -> TutorialState:
        """Generate initial tutorial content for the subject."""
        subject = state["subject"]
        language = state.get("language", "English")
        
        prompt = f"""You are an expert AI tutor. Create a comprehensive but concise tutorial about {subject}.
        
        IMPORTANT: Write the entire response in {language}.

Structure your response as follows:
1. Brief introduction to the topic
2. Key concepts and definitions
3. Important examples
4. Common applications or use cases
5. Tips for further learning

Keep the tutorial engaging, educational, and appropriate for beginners to intermediate learners.
Use clear examples and explanations. Aim for about 200-300 words for a faster, more digestible start.

formatting instructions: 
- Use **BOLD** for all key terms, important words, and subtopic headers.
- Use bullet points for lists.
- Highlighting important concepts is CRITICAL. Use standard Markdown formatting."""

        response = self._call_llm(prompt)
        
        # Save to database
        self.db.add_message(
            state["conversation_id"], 
            "assistant", 
            response, 
            "tutorial"
        )
        
        tutorial_message = AIMessage(content=response)
        
        return {
            **state,
            "messages": state["messages"] + [tutorial_message],
            "current_mode": "qa"
        }

    def _retrieve_knowledge(self, state: TutorialState) -> dict:
        """Retrieve relevant context from the knowledge base."""
        # Get the latest user question
        last_message = state["messages"][-1]
        query = last_message.content
        
        # Use RAG engine facade to get formatted context
        # Note: We are using the facade's helper which returns a string "CONTEXT FROM..."
        # We store this in the state.
        context = self.rag_engine.get_formatted_context(query)
        
        return {"retrieved_context": context}
    
    def _handle_question(self, state: TutorialState) -> TutorialState:
        """Handle user questions about the tutorial content."""
        subject = state["subject"]
        user_question = state["messages"][-1].content
        language = state.get("language", "English")
        
        # Get conversation context
        context_messages = state["messages"][-5:]  # Last 5 messages for context
        context = "\n".join([f"{msg.__class__.__name__[:-7]}: {msg.content}" for msg in context_messages])
        
        context = "\n".join([f"{msg.__class__.__name__[:-7]}: {msg.content}" for msg in context_messages])
        
        # Get RAG context from state (populated by _retrieve_knowledge node)
        rag_context = state.get("retrieved_context", "")
        
        prompt = f"""You are a helpful, ethical AI tutor teaching about {subject}.

RULES:
1. Answer EXACTLY what the user asks - no more, no less
2. Be direct and concise - avoid unnecessary explanations
3. Be ethical and honest
4. Write your response in {language}

Previous context:
{context}

{rag_context}

User's question: "{user_question}"

If there is relevant context from uploaded documents, use it and cite it briefly.
Provide a direct, focused answer."""

        response = self._call_llm(prompt)
        
        # Save to database
        self.db.add_message(
            state["conversation_id"], 
            "user", 
            user_question, 
            "question"
        )
        self.db.add_message(
            state["conversation_id"], 
            "assistant", 
            response, 
            "answer"
        )
        
        answer_message = AIMessage(content=response)
        
        return {
            **state,
            "messages": state["messages"] + [answer_message],
            "current_mode": "qa"
        }
    
    def _create_evaluation(self, state: TutorialState) -> TutorialState:
        """Create evaluation questions to test user understanding."""
        subject = state["subject"]
        evaluation_count = state.get("evaluation_count", 0)
        
        # Get tutorial content for context
        tutorial_content = ""
        for msg in state["messages"]:
            if isinstance(msg, AIMessage):
                tutorial_content += msg.content + "\n"
        
        prompt = f"""You are an expert AI tutor. Based on the tutorial content about {subject}, create a thoughtful evaluation question.

Tutorial content covered:
{tutorial_content[:1000]}...

Create ONE evaluation question that:
1. Tests understanding of key concepts
2. Is neither too easy nor too difficult
3. Requires the student to demonstrate comprehension
4. Can be answered in 1-3 sentences

Format your response as:
QUESTION: [Your question here]

This is evaluation question #{evaluation_count + 1}."""

        response = self._call_llm(prompt)
        
        # Save to database
        self.db.add_message(
            state["conversation_id"], 
            "assistant", 
            response, 
            "evaluation_question"
        )
        
        eval_message = AIMessage(content=response)
        
        return {
            **state,
            "messages": state["messages"] + [eval_message],
            "current_mode": "evaluation",
            "evaluation_count": evaluation_count + 1
        }
    
    def _evaluate_answer(self, state: TutorialState) -> TutorialState:
        """Evaluate user's answer to evaluation question."""
        subject = state["subject"]
        user_answer = state["messages"][-1].content
        eval_question = state["messages"][-2].content
        
        prompt = f"""You are an expert AI tutor evaluating a student's answer about {subject}.

Evaluation Question: {eval_question}
Student's Answer: {user_answer}

Provide constructive feedback that:
1. Acknowledges what the student got right
2. Gently corrects any misconceptions
3. Provides additional clarification if needed
4. Encourages continued learning

Be supportive and educational. Rate their understanding and provide specific feedback."""

        response = self._call_llm(prompt)
        
        # Save to database
        self.db.add_message(
            state["conversation_id"], 
            "user", 
            user_answer, 
            "evaluation_answer"
        )
        self.db.add_message(
            state["conversation_id"], 
            "assistant", 
            response, 
            "evaluation_feedback"
        )
        
        feedback_message = AIMessage(content=response)
        
        return {
            **state,
            "messages": state["messages"] + [feedback_message],
            "current_mode": "qa"
        }
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM using the existing API setup."""
        from LLM_api import DEFAULT_MODEL, LLM_PROVIDER
        try:
            print(f"DEBUG: Calling LLM ({LLM_PROVIDER}: {DEFAULT_MODEL})...")
            completion = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            
            if completion and hasattr(completion, 'choices') and completion.choices:
                return completion.choices[0].message.content
            return "Error: No response from AI provider."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _call_llm_stream(self, prompt: str):
        """Stream LLM response chunk by chunk."""
        from LLM_api import DEFAULT_MODEL
        try:
            stream = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def _route_after_tutorial(self, state: TutorialState) -> str:
        """Route after tutorial generation - wait for user input."""
        return "end"  # End and wait for user input
    
    def _route_after_question(self, state: TutorialState) -> str:
        """Route after handling a question."""
        return "end"  # End and wait for user input
    
    def _route_after_evaluation(self, state: TutorialState) -> str:
        """Route after creating evaluation question."""
        return "end"  # End and wait for user answer
    
    def _route_after_evaluation_answer(self, state: TutorialState) -> str:
        """Route after evaluating user's answer."""
        return "end"  # End and wait for next user input
    
    def start_tutorial(self, session_id: str, subject: str, language: str = "English") -> Dict[str, Any]:
        """Start a new tutorial session."""
        # Create conversation in database
        conversation_id = self.db.create_conversation(session_id, subject)
        
        # Initialize state
        initial_state = TutorialState(
            messages=[],
            subject=subject,
            conversation_id=conversation_id,
            current_mode="tutorial",
            evaluation_count=0,
            user_understanding={},
            language=language,
            context="" # Initialize RAG context
        )
        
        # Generate tutorial
        result = self.graph.invoke(initial_state)
        
        return {
            "conversation_id": conversation_id,
            "response": result["messages"][-1].content,
            "mode": result["current_mode"]
        }
    
    def continue_conversation(self, conversation_id: int, user_input: str, input_type: str = "question", language: str = "English", context: str = "") -> Dict[str, Any]:
        """Continue an existing conversation."""
        # Get conversation history
        history = self.db.get_conversation_history(conversation_id)
        
        # Reconstruct state
        messages = []
        conversation_info = None
        
        # Get conversation info from database
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT subject FROM conversations WHERE id = ?", (conversation_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {"error": "Conversation not found"}
        
        subject = result[0]
        
        # Convert history to messages
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Add new user message
        messages.append(HumanMessage(content=user_input))
        
        # Determine current state
        current_mode = "qa"
        evaluation_count = len([msg for msg in history if msg.get("message_type") == "evaluation_question"])
        
        # Check if this is an evaluation answer
        if history and history[-1].get("message_type") == "evaluation_question":
            current_mode = "evaluation_answer"
        
        state = TutorialState(
            messages=messages,
            subject=subject,
            conversation_id=conversation_id,
            current_mode=current_mode,
            evaluation_count=evaluation_count,
            user_understanding={},
            language=language,
            context=context # Pass RAG context
        )
        
        # Process based on input type and current mode
        if current_mode == "evaluation_answer":
            result = self._evaluate_answer(state)
        elif input_type == "evaluation_request":
            result = self._create_evaluation(state)
        else:
            # IMPORTANT: Call RAG retrieval FIRST to populate context
            rag_update = self._retrieve_knowledge(state)
            state = {**state, **rag_update}  # Merge retrieved context into state
            result = self._handle_question(state)
        
        return {
            "response": result["messages"][-1].content,
            "mode": result["current_mode"]
        }