import streamlit as st
import openai
import os
import requests
import json
import uuid
import datetime
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

# URL do webhook Make
WEBHOOK_URL = "https://hook.us2.make.com/iu7sc1vc4254f29zop2f6j8e24a4dnj4"

# Função para enviar dados para o webhook do Make
def send_to_webhook(user_info, last_message, last_response):
    try:
        # Estrutura exata conforme solicitada no prompt do Make
        # Apenas JSON puro com nome, email e mensagem
        payload = {
            "nome": user_info["name"],
            "email": user_info["email"],
            "mensagem": last_message
        }
        
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10  # Timeout de 10 segundos
        )
        
        if response.status_code == 200:
            return True
        else:
            st.sidebar.error(f"Erro ao enviar dados: {response.status_code}")
            return False
    except Exception as e:
        st.sidebar.error(f"Erro na comunicação com webhook: {str(e)}")
        return False

# Inicialização da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = ""
    
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
    
if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "name": "",
        "email": "",
        "phone": ""
    }

# Título principal
st.title("ChatBot com OpenAI Assistant")

# Sidebar para configurações
st.sidebar.title("Configurações")

# Campo para o ID do assistente
assistant_id = st.sidebar.text_input("ID do Assistente OpenAI", value=st.session_state.assistant_id)
if assistant_id != st.session_state.assistant_id:
    st.session_state.assistant_id = assistant_id
    
# Informações do usuário para leads
st.sidebar.title("Suas Informações")
st.sidebar.markdown("Preencha para salvar seus dados de contato")

user_name = st.sidebar.text_input("Nome", value=st.session_state.user_info["name"])
user_email = st.sidebar.text_input("Email", value=st.session_state.user_info["email"])
user_phone = st.sidebar.text_input("Telefone", value=st.session_state.user_info["phone"])

# Atualiza as informações do usuário
if (user_name != st.session_state.user_info["name"] or 
    user_email != st.session_state.user_info["email"] or 
    user_phone != st.session_state.user_info["phone"]):
    
    st.session_state.user_info["name"] = user_name
    st.session_state.user_info["email"] = user_email
    st.session_state.user_info["phone"] = user_phone

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
                    
                    # Enviar dados ao webhook se tiver pelo menos o email
                    if st.session_state.user_info["email"]:
                        success = send_to_webhook(
                            st.session_state.user_info,
                            prompt,
                            content
                        )
                        if success:
                            st.sidebar.success("Mensagem registrada!", icon="✅")
                    
                    # Reexibir as mensagens com a resposta
                    display_messages()
                else:
                    st.error("Não foi possível obter uma resposta do assistente.")
                    
            except Exception as e:
                st.error(f"Erro ao comunicar com a API da OpenAI: {str(e)}")

# Botões de ação
col1, col2 = st.columns(2)

with col1:
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.session_state.conversation_id = str(uuid.uuid4())  # Gera novo ID de conversa
        st.experimental_rerun()

with col2:
    if st.button("Salvar Conversa"):
        if not st.session_state.user_info["email"]:
            st.error("Por favor, preencha pelo menos seu email para salvar a conversa.")
        elif len(st.session_state.messages) < 2:
            st.warning("Ainda não há mensagens suficientes para salvar.")
        else:
            # Encontrar a última troca de mensagens
            last_user_msg = ""
            last_assistant_msg = ""
            
            for msg in reversed(st.session_state.messages):
                if msg["role"] == "assistant" and not last_assistant_msg:
                    last_assistant_msg = msg["content"]
                elif msg["role"] == "user" and not last_user_msg:
                    last_user_msg = msg["content"]
                
                if last_user_msg and last_assistant_msg:
                    break
            
            # Enviar ao webhook
            if send_to_webhook(
                st.session_state.user_info,
                last_user_msg,
                last_assistant_msg
            ):
                st.success("Conversa salva com sucesso!")
            else:
                st.error("Erro ao salvar conversa. Tente novamente.")

# Informações adicionais
st.sidebar.markdown("---")
st.sidebar.markdown("""
### Como usar:
1. Insira sua API key da OpenAI
2. Insira o ID do seu assistente
3. Preencha suas informações de contato para salvar suas conversas
4. Converse com o chatbot!

Para criar um assistente, visite o [OpenAI Playground](https://platform.openai.com/playground).
""")

# Informações sobre o webhook
st.sidebar.markdown("---")
st.sidebar.markdown("""
### Integração com Make (Webhook)
As conversas são salvas automaticamente quando:
- Você fornece pelo menos seu email
- O assistente envia uma resposta

Você também pode salvar manualmente usando o botão "Salvar Conversa".
""")
