import streamlit as st
import openai
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente (opcional, para segurança)
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="ChatBot OpenAI",
    page_icon="🤖",
    layout="centered"
)

# Estilo CSS
st.markdown("""
<style>
.chat-message {
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 10px;
    display: flex;
    flex-direction: row;
    color: black;
    font-weight: 500;
}
.chat-message.user {
    background-color: #e6e6e6;
    border-left: 5px solid #2e72ea;
}
.chat-message.assistant {
    background-color: #f5f5f5;
    border-left: 5px solid #10a37f;
}
.chat-message .avatar {
    width: 10%;
    display: flex;
    align-items: center;
    justify-content: center;
}
.chat-message .content {
    width: 90%;
}
.chat-message .avatar img {
    max-width: 40px;
    max-height: 40px;
    border-radius: 50%;
    object-fit: cover;
}
.content p {
    font-size: 16px;
    line-height: 1.5;
    color: #000000;
}
</style>
""", unsafe_allow_html=True)

# Função para obter a API key
def get_openai_api_key():
    # Tenta obter a API key do ambiente
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Se não encontrar no ambiente, pede ao usuário
    if not api_key:
        api_key = st.sidebar.text_input("OpenAI API Key", type="password")
        if not api_key:
            st.sidebar.warning("Por favor, insira sua API key para continuar.")
    
    return api_key

# Inicialização da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = ""

# Sidebar para configurações
st.sidebar.title("Configurações")

# Campo para o ID do assistente
assistant_id = st.sidebar.text_input("ID do Assistente OpenAI", value=st.session_state.assistant_id)
if assistant_id != st.session_state.assistant_id:
    st.session_state.assistant_id = assistant_id

# Título principal
st.title("ChatBot com OpenAI Assistant")

# Obtenção da API key
api_key = get_openai_api_key()

# Função para exibir mensagens
def display_messages():
    for message in st.session_state.messages:
        with st.container():
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                avatar = "👤"
                bg_color = "user"
                name = "Você"
            else:
                avatar = "🤖"
                bg_color = "assistant"
                name = "Assistente"
                
            st.markdown(f"""
            <div class="chat-message {bg_color}">
                <div class="avatar">
                    <p>{avatar}</p>
                </div>
                <div class="content">
                    <strong>{name}</strong>
                    <p>{content}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Exibir histórico de mensagens
display_messages()

# Campo de entrada para nova mensagem
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    # Verificar se todas as configurações necessárias estão disponíveis
    if not api_key:
        st.error("Por favor, insira sua API key na barra lateral.")
    elif not assistant_id:
        st.error("Por favor, insira o ID do seu assistente na barra lateral.")
    else:
        # Adicionar mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Reexibir as mensagens com a nova do usuário
        with st.spinner("Pensando..."):
            try:
                # Configurar cliente da OpenAI
                client = openai.OpenAI(api_key=api_key)
                
                # Criar um thread
                thread = client.beta.threads.create()
                
                # Adicionar a mensagem do usuário ao thread
                client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=prompt
                )
                
                # Executar o assistente com o thread
                run = client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=assistant_id
                )
                
                # Esperar a conclusão da execução
                while run.status in ["queued", "in_progress"]:
                    run = client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Recuperar as mensagens do thread
                messages = client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                # Obter a resposta mais recente do assistente
                assistant_message = None
                for message in messages.data:
                    if message.role == "assistant":
                        assistant_message = message
                        break
                
                if assistant_message:
                    content = assistant_message.content[0].text.value
                    st.session_state.messages.append({"role": "assistant", "content": content})
                    # Reexibir as mensagens com a resposta
                    display_messages()
                else:
                    st.error("Não foi possível obter uma resposta do assistente.")
                    
            except Exception as e:
                st.error(f"Erro ao comunicar com a API da OpenAI: {str(e)}")

# Botão para limpar o histórico
if st.button("Limpar Conversa"):
    st.session_state.messages = []
    st.experimental_rerun()

# Informações adicionais
st.sidebar.markdown("---")
st.sidebar.markdown("""
### Como usar:
1. Insira sua API key da OpenAI
2. Insira o ID do seu assistente
3. Converse com o chatbot!

Para criar um assistente, visite o [OpenAI Playground](https://platform.openai.com/playground).
""")
