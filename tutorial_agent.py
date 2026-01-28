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
        
        # Always provide educational content about the subject
        prompt = f"""You are Socrates, an AI tutor who teaches about {subject}.
        
        IMPORTANT: Write the entire response in {language}.

YOUR GOAL: Provide a welcoming, educational introduction to {subject} that TEACHES real content.

STRUCTURE YOUR TUTORIAL INTRODUCTION:
1. **Welcome & Hook** (1-2 sentences): Greet the student warmly and share why {subject} is fascinating/important
2. **Core Concept Overview** (3-4 sentences): Explain what {subject} is in simple, clear terms. Give a real definition.
3. **Key Fundamentals** (bullet points): List 3-4 fundamental concepts or components they'll learn about
4. **Engaging Example** (2-3 sentences): Provide a real-world example or analogy that makes the concept relatable
5. **Interactive Close** (1 question): End with ONE thought-provoking question to start the conversation

IMPORTANT RULES:
- You MUST teach actual content, not just ask questions!
- Provide real definitions and explanations
- Make it educational, not just a list of questions
- Keep it engaging but substantive

FORMATTING:
- Use **bold** for key terms and concepts
- Use bullet points for lists
- Aim for 200-300 words
- End with ONE open question for the student to respond to

Remember: Students are here to LEARN. Give them knowledge to work with!"""

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
        
        prompt = f"""You are Socrates, an AI tutor who teaches about {subject}.

IMPORTANT: Write your response in {language}.

YOUR TEACHING APPROACH & INTERACTION LOGIC:
1. **CRITICAL: Explicit Topic Advancement**: If the student affirms your previous suggestion (e.g., "yes", "proceed", "continue"):
   - **Immediately** begin teaching the **specific sub-topic** suggested in the previous turn.
   - **DO NOT** repeat the broad definition of {subject} or provide a general introductory summary.
   - Assume the student has mastered what was discussed in `Previous context` and move **forward**.

2. **Contextual Quiz Mode**: 
   - Generate 3 specific questions based *only* on context already taught in this session.
   - No introductory filler. No answers.

3. **Logical Pathing (Suggestions)**: 
   - Every response **MUST END** by suggesting the **next logical sub-topic** as a question (e.g., "Now that we've covered the basics of X, would you like to explore **Y** next?").

CRITICAL RULES:
- **NO REPETITION**: Do not explain concepts that are already present in the `Previous context`.
- **NO CASUAL GREETINGS**.
- **START IMMEDIATELY**: Dive deep into the specific sub-topic.

RESPONSE STRUCTURE:
- Direct explanation/answer of the specific sub-topic with **bold** terms.
- Concrete example or professional analogy.
- **Suggestion**: End with the question proposing the next logical step in the curriculum.

Previous context:
{context}

{rag_context}

Student's message: "{user_question}"

IMPORTANT: You must TEACH! Provide real knowledge and explanations.
If there is relevant context from uploaded documents, use it in your response."""

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
        
        prompt = f"""You are Socrates, an AI tutor using the SOCRATIC METHOD to provide feedback about {subject}.

Evaluation Question: {eval_question}
Student's Answer: {user_answer}

SOCRATIC FEEDBACK APPROACH:
1. Acknowledge their thinking process (not just correctness)
2. If correct: Ask a deeper follow-up question to extend understanding
3. If partially correct: Use guiding questions to help them discover what's missing
4. If incorrect: Don't say "wrong" - instead ask questions that reveal the gap
5. Always encourage their reasoning, even when correcting

EXAMPLE RESPONSES:
- "Interesting thinking! What made you arrive at that conclusion?"
- "You're on the right track. Now, what if we consider...?"
- "I see your reasoning. Let's explore this further - what do you think would happen if...?"

Your feedback should:
- Validate their effort
- Guide them to deeper understanding through questions
- Not give away the complete answer if they were wrong
- Encourage them to try again or think further

Be supportive and use the Socratic method to help them learn from this attempt."""

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