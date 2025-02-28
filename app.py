import gradio as gr
from config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW, ROLES, init_openai_client
from userAuth import UserAuth
from RateLimiter import RateLimiter

from vectorDocumentStore import VectorDocumentStore
from utils import add_sample_documents
from RagChat import RAGChat

client = init_openai_client()
print("initialized openai_client")
user_auth = UserAuth()
print("initialized User Auth")
doc_store = VectorDocumentStore(client)
print("initialized Vector data store")
rag_chat = RAGChat(client, doc_store)
print("initialized Rag Chat")
rate_limiter = RateLimiter()

if not any(doc_store.list_documents(role) for role in ROLES):
    add_sample_documents(doc_store)
# print([doc_store.list_documents(role) for role in ROLES])

with gr.Blocks(title="Role-Based RAG System") as demo:
    session_token = gr.State("")
    current_user = gr.State("")
    current_role = gr.State("")
    gr.Markdown("# Role-Based RAG System")
    
    with gr.Tab("Login"):
        gr.Markdown("## User Login")
        username = gr.Textbox(label="Username")
        password = gr.Textbox(label="Password", type="password")
        login_msg = gr.Markdown("")
        
        login_btn = gr.Button("Login")
        def login_user(username, password):
            result = user_auth.authenticate(username, password)
            if result:
                token, role = result
                return token, username, role, f"Logged in as {username} with role: {role}"
            return "", "", "", "Login failed. Check your credentials or account may be locked."
        login_btn.click(
            fn=login_user, 
            inputs=[username, password], 
            outputs=[session_token, current_user, current_role, login_msg]
        )
        
        logout_btn = gr.Button("Logout")
        def logout(token):
            if token:
                user_auth.logout(token)
                return "", "", "", "Logged out successfully."
            return "", "", "", "Not logged in."
        logout_btn.click(
            fn=logout,
            inputs=[session_token],
            outputs=[session_token, current_user, current_role, login_msg]
        )

    with gr.Tab("Chat"):
        user_info = gr.Markdown("Please login first")
        doc_list = gr.Markdown("No documents available")
        def update_user_info(token, user, role):
            if token and user and role:
                session_result = user_auth.validate_session(token)
                if not session_result:
                    return "Session expired. Please login again.", "No documents available", "", "", ""                
                docs = doc_store.list_documents(role)
                doc_text = "## Available Documents\n" + "\n".join([f"- {doc}" for doc in docs]) if docs else "No documents available for your role"
                return f"## Logged in as: {user} (Role: {role})", doc_text
            return "Please login first", "No documents available"
        
        session_token.change(
            fn=update_user_info, 
            inputs=[session_token, current_user, current_role], 
            outputs=[user_info, doc_list]
        )
        
        chat_interface = gr.Chatbot(height=400, label="Chat")
        query = gr.Textbox(label="Your question")
        send_btn = gr.Button("Send")
        clear_btn = gr.Button("Clear")
        rate_limit_info = gr.Markdown("")
        
        def respond(token, user, role, question, history):
            if not token or not user or not role:
                return history + [["Please login first", ""]], "Please login to continue."
            
            session_result = user_auth.validate_session(token)
            if not session_result:
                return history + [["Session expired", "Your session has expired. Please login again."]], "Session expired. Please login again."
            
            if not rate_limiter.check_rate_limit(user):
                limit_msg = f"Rate limit exceeded. You can make {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
                return history + [[question, "Rate limit exceeded. Please try again later."]], limit_msg
            
            rate_info = f"Requests remaining: {RATE_LIMIT_MAX_REQUESTS - len(rate_limiter.user_requests.get(user, []))} per {RATE_LIMIT_WINDOW} seconds"
            
            response = rag_chat.chat(role, question)
            return history + [[question, response]], rate_info
        
        send_btn.click(
            fn=respond,
            inputs=[session_token, current_user, current_role, query, chat_interface],
            outputs=[chat_interface, rate_limit_info],
            queue=False
        ).then(
            fn=lambda: "", 
            inputs=None, 
            outputs=[query]
        )

        def clear_chat():
            return [], ""
        
        clear_btn.click(fn=clear_chat, inputs=None, outputs=[chat_interface, rate_limit_info])
    
    with gr.Tab("Admin"):
        admin_info = gr.Markdown("Admin panel - requires admin access")
        
        def check_admin(token, user, role):
            if not token:
                return "## Admin Panel\nPlease login first."
            
            # Validate session
            session_result = user_auth.validate_session(token)
            if not session_result:
                return "## Admin Panel\nSession expired. Please login again."
            
            if role == "admin":
                return "## Admin Panel\nYou have access to admin features."
            return "## Admin Panel\nYou need admin privileges to access this section."
        
        session_token.change(fn=check_admin, inputs=[session_token, current_user, current_role], outputs=[admin_info])
        
        with gr.Accordion("User Management", open=False):
            new_user = gr.Textbox(label="New Username")
            new_pass = gr.Textbox(label="New Password", type="password")
            new_role = gr.Dropdown(label="Role", choices=ROLES)
            add_user_btn = gr.Button("Add User")
            user_result = gr.Markdown("")
            
            def add_new_user(token, current_role, username, password, role):
                if not token:
                    return "Please login first."
                
                session_result = user_auth.validate_session(token)
                if not session_result:
                    return "Session expired. Please login again."
                
                if current_role != "admin":
                    return "You need admin privileges."
                
                success = user_auth.add_user(username, password, role)
                if success:
                    return f"✅ Added user {username} with role {role}"
                return f"❌ Failed to add user {username}"
            
            add_user_btn.click(
                fn=add_new_user,
                inputs=[session_token, current_role, new_user, new_pass, new_role],
                outputs=[user_result]
            )
            
            list_users_btn = gr.Button("List Users")
            user_list =gr.Markdown("")
            
            def list_all_users(current_user, current_role):
                if not current_user or current_role != "admin":
                    return "You need admin privileges."
                
                users = user_auth.list_users()
                result = "## User List\n"
                for username, role in users.items():
                    result += f"- {username}: {role}\n"
                return result
            
            list_users_btn.click(
                fn=list_all_users,
                inputs=[current_user, current_role],
                outputs=[user_list]
            )
        
        with gr.Accordion("Document Management", open=False):
            doc_title = gr.Textbox(label="Document Title")
            doc_role = gr.Dropdown(label="Document Role", choices=ROLES)
            doc_content = gr.Textbox(label="Document Content", lines=10)
            add_doc_btn = gr.Button("Add Document")
            doc_result = gr.Markdown("")
            
            def add_new_document(current_user, current_role, title, role, content):
                if not current_user or current_role != "admin":
                    return "You need admin privileges."
                
                success = doc_store.add_document(role, title, content)
                if success:
                    return f"✅ Added document '{title}' for role {role}"
                return f"❌ Failed to add document"
            
            add_doc_btn.click(
                fn=add_new_document,
                inputs=[current_user, current_role, doc_title, doc_role, doc_content],
                outputs=[doc_result]
            )
demo.launch(share=True)


