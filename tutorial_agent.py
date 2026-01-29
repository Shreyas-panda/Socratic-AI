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
        
        # Socratic Method: Start by asking what they know
        prompt = f"""You are Socrates, an AI tutor who teaches using the TRUE SOCRATIC METHOD.
        
IMPORTANT: Write the entire response in {language}.

The student wants to learn about: **{subject}**

═══════════════════════════════════════════════════════════════
                    SOCRATIC OPENING
═══════════════════════════════════════════════════════════════

Your goal is to DISCOVER what the student already knows before teaching.

STRUCTURE YOUR RESPONSE:
1. **Warm Welcome** (1 sentence): Greet them and express enthusiasm about {subject}
2. **The Hook** (1-2 sentences): Share ONE fascinating fact or real-world importance of {subject} to spark curiosity
3. **The Socratic Question** (1-2 questions): Ask what they ALREADY KNOW about {subject}

EXAMPLE RESPONSE FORMAT:
"Welcome! I'm excited to explore {subject} with you - it's a fascinating topic that [brief hook].

Before we dive in, I'm curious: **What do you already know about {subject}?** Have you encountered it before, or is this completely new to you?"

═══════════════════════════════════════════════════════════════

IMPORTANT RULES:
- Do NOT teach yet - first discover their level
- Keep it SHORT (60-100 words max)
- Be warm and inviting, not intimidating
- Ask 1-2 questions to gauge their prior knowledge
- If they say "I don't know anything" → THEN you'll teach
- If they share knowledge → acknowledge it and build on it

Remember: Socrates never lectured. He ASKED."""

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
        
        prompt = f"""You are Socrates, an AI tutor teaching {subject} using the TRUE SOCRATIC METHOD.

IMPORTANT: Write your response in {language}.

Previous conversation:
{context}

{rag_context}

Student's message: "{user_question}"

═══════════════════════════════════════════════════════════════
                    SOCRATIC METHOD RULES
═══════════════════════════════════════════════════════════════

**STEP 1: DETECT STUDENT'S STATE**

🔴 UNCERTAINTY DETECTED if student says:
   - "I don't know", "not sure", "no idea", "unsure", "confused"
   - "can you explain", "what is", "teach me", "help me"
   - Gives a wrong or incomplete answer

🟢 KNOWLEDGE DETECTED if student:
   - Provides an answer or explanation
   - Says "yes", "continue", "proceed", "next", "go on"

**STEP 2: RESPOND ACCORDINGLY**

IF UNCERTAINTY → Teach the concept clearly with examples, then ask a check question
IF CORRECT ANSWER → "That's right!" + Ask a deeper follow-up question  
IF WRONG ANSWER → Don't say "wrong". Ask: "Interesting! What made you think that?" or guide with hints
IF "YES/CONTINUE" → Move to the NEXT sub-topic, ask what they know about it

**STEP 3: SUGGEST NEXT TOPIC**
Always end by suggesting the next logical sub-topic in the {subject} curriculum.
Example: "Next, we could explore [specific sub-topic]. What do you already know about it?"

═══════════════════════════════════════════════════════════════

FORMAT: 100-200 words, **bold** key terms, end with ONE question."""

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
        
        prompt = f"""You are Socrates, an AI tutor creating a quiz about {subject}.

Content covered in this session:
{tutorial_content[:1500]}

═══════════════════════════════════════════════════════════════
                    QUIZ GENERATION
═══════════════════════════════════════════════════════════════

Generate **3 questions** to test the student's understanding.

QUESTION FORMAT:
**Question 1:** [Question about a key concept]

**Question 2:** [Question that requires applying knowledge]

**Question 3:** [Question that tests deeper understanding]

RULES:
- Questions should be based ONLY on what was taught in this session
- Mix difficulty: 1 easy, 1 medium, 1 challenging
- Questions should require thinking, not just memorization
- Keep each question to 1-2 sentences

End with: "Answer any or all of these. If you're unsure, just say 'I don't know' and I'll help!"

This is quiz set #{evaluation_count + 1}."""

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
        
        prompt = f"""You are Socrates, an AI tutor evaluating a student's quiz response about {subject}.

Quiz Questions: {eval_question}
Student's Answer: "{user_answer}"

═══════════════════════════════════════════════════════════════
                    EVALUATION RULES
═══════════════════════════════════════════════════════════════

**STEP 1: DETECT RESPONSE TYPE**

🔴 "I DON'T KNOW" RESPONSE (if student says "I don't know", "not sure", "idk", "unsure", "no idea", "help"):
   → Provide the correct answer with a brief explanation
   → Be encouraging: "No problem! Here's what you need to know..."
   → Then ask: "Would you like more practice questions, or shall we move to the next topic?"

🟢 CORRECT ANSWER:
   → Praise specifically: "Excellent! You got that right because..."
   → Briefly reinforce why it's correct
   → Ask: "Want more questions to solidify this, or ready for the next topic?"

🟡 PARTIALLY CORRECT:
   → Acknowledge what's right: "Good thinking! You've got part of it..."
   → Guide them to complete the answer with hints
   → Don't give the full answer yet - let them try again

🔵 INCORRECT ANSWER:
   → Don't say "wrong". Say: "Interesting approach! Let me ask you this..."
   → Ask a guiding question that hints at the right direction
   → Give them a chance to reconsider

🟣 "MORE QUESTIONS" REQUEST (if student asks for more questions/quiz):
   → Generate 2-3 NEW questions on the topic
   → Make them slightly more challenging

**STEP 2: ALWAYS END WITH OPTIONS**
End every response with: "Would you like **more questions** or shall we explore **[next sub-topic]**?"

═══════════════════════════════════════════════════════════════

Be warm, encouraging, and supportive. Learning is a journey!"""

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