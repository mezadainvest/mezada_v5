import streamlit as st
import matplotlib.pyplot as plt
import urllib.parse  # Para codificar a mensagem corretamente
import pandas as pd
import os
#import login3  # Importa o sistema de login com Firebase
from dotenv import load_dotenv
from groq import Groq  # Para chamar Llama 3 via Groq
import sqlite3


load_dotenv()

GROQ_API_KEY = os.getenv("model_groq_api_key")
groq_client = Groq(api_key=GROQ_API_KEY)

# Nome do arquivo do banco de dados
db_name = "usuarios.db"









# Configuração do banco de dados de usuários
def inicializar_banco_dados_usuarios():
    # Verifica se o arquivo do banco de dados existe
    if not os.path.exists(db_name):
        print(f"Banco de dados '{db_name}' não encontrado. Criando um novo...")

        # Conecta ao banco de dados (isso criará o arquivo automaticamente)

        conn = sqlite3.connect('usuarios.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id TEXT UNIQUE,
                historia_usuario TEXT,
                contexto_livros TEXT,
                perfil_investimento TEXT,
                niveis_completos INTEGER DEFAULT 0,
                checklist TEXT DEFAULT '{}'  -- Armazena o checklist como JSON
            )
        ''')
        # Salva as alterações e fecha a conexão
        conn.commit()
        conn.close()
        print(f"Banco de dados '{db_name}' criado com sucesso!")
    else:
        print(f"Banco de dados '{db_name}' já existe.")


# Salvar ou atualizar o progresso do usuário no banco de dados
def salvar_progresso(usuario_id, historia_usuario, contexto_livros, perfil_investimento, niveis_completos, checklist):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO usuarios (usuario_id, historia_usuario, contexto_livros, perfil_investimento, niveis_completos, checklist)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (usuario_id, historia_usuario, contexto_livros, perfil_investimento, niveis_completos, str(checklist)))
    conn.commit()
    conn.close()


# Recuperar o progresso do usuário do banco de dados
def recuperar_progresso(usuario_id):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE usuario_id = ?', (usuario_id,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return {
            "usuario_id": resultado[1],
            "historia_usuario": resultado[2],
            "contexto_livros": resultado[3],
            "perfil_investimento": resultado[4],
            "niveis_completos": resultado[5],
            "checklist": eval(resultado[6])  # Converte o checklist de string para dicionário
        }
    return None


# Recuperar resumos de livros do banco de dados pré-processado
def recuperar_resumos_livros():
    conn = sqlite3.connect('livros.db')
    cursor = conn.cursor()
    cursor.execute('SELECT titulo, resumo FROM livros')
    resultados = cursor.fetchall()
    conn.close()
    return {titulo: resumo for titulo, resumo in resultados}


# Função para identificar o perfil de investimento do usuário
def identificar_perfil_investimento(historia_usuario, contexto_livros):
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""
    Você é um assistente especializado em análise de perfis de investimento.
    Com base na seguinte história de vida do usuário e no contexto adicional fornecido, identifique o perfil de investimento dele:

    História do usuário: {historia_usuario}

    Contexto adicional (extraído de livros): {contexto_livros}

    Baseando-se nesses dados, gere:
    1. O perfil de investimento do usuário (Conservador, Moderado ou Agressivo).
    2. Recomendações de investimentos adequados ao perfil.
    """
    resposta = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Você é um assistente especializado em análise de perfis de investimento."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    return resposta.choices[0].message.content


# Função para sugerir metas personalizadas usando LLM
def sugerir_metas(perfil_investimento, historia_usuario):
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""
    Você é um assistente especializado em planejamento financeiro.
    Com base no perfil de investimento do usuário e na história dele, sugira metas financeiras personalizadas para o próximo nível da jornada gamificada:

    Perfil de Investimento: {perfil_investimento}
    História do Usuário: {historia_usuario}

    Sugira metas claras e alcançáveis para o próximo nível, divididas em tarefas específicas.
    """
    resposta = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Você é um assistente especializado em planejamento financeiro."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    return resposta.choices[0].message.content

##################################





#####################################

# Função para exibir o gráfico de progresso
def exibir_grafico_progresso(niveis_completos, niveis_totais):
    fig, ax = plt.subplots()
    niveis = ["Nível " + str(i + 1) for i in range(niveis_totais)]
    completos = [1 if i < niveis_completos else 0 for i in range(niveis_totais)]

    ax.bar(niveis, completos, color=['green' if c == 1 else 'gray' for c in completos])
    ax.set_title("Progresso na Jornada")
    ax.set_ylabel("Completado")
    plt.xticks(rotation=45)
    st.pyplot(fig)


# Página de Análise Psicológica
def pagina_analise_psicologica():
    #st.title("Mezada 1.0")
    st.title("Mezada 1.0 - Análise Perfil Financeiro")

    # Recuperar resumos dos livros do banco de dados
    resumos_livros = recuperar_resumos_livros()
    contexto_livros = "\n".join([f"Livro: {titulo}\nResumo: {resumo}" for titulo, resumo in resumos_livros.items()])

    # Entrada do usuário
    historia_usuario = st.text_area("Conte sua história de vida relacionada a finanças:",
                                    value="Sempre tive dificuldades para economizar. Quando era jovem, meus pais tiveram problemas financeiros e isso me deixou ansioso sobre dinheiro.")

    # Botão para iniciar a análise
    if st.button("Analisar"):
        with st.spinner("Realizando análise..."):
            resultado = identificar_perfil_investimento(historia_usuario, contexto_livros)

        # Exibe o resultado completo
        st.subheader("Diagnóstico e Recomendações:")
        st.write(resultado)

        # Salva o progresso no banco de dados
        usuario_id = st.session_state.get("usuario_id", "usuario123")  # Use um ID padrão ou permita entrada
        salvar_progresso(usuario_id, historia_usuario, contexto_livros, resultado, 0, {})


# Página de Jornada de Investimento
def pagina_jornada_investimento():
    #st.title("Mezada 1.0")
    st.title("Mezada 1.0 - Jornada de Investimento e Gamificação")

    # Identificação do usuário
    usuario_id = st.text_input("Digite seu ID de Usuário:", value="usuario123")

    # Inicializar banco de dados
    inicializar_banco_dados_usuarios()

    # Recuperar progresso do usuário
    progresso = recuperar_progresso(usuario_id)
    if not progresso or not progresso["historia_usuario"] or not progresso["contexto_livros"]:
        st.warning("Por favor, complete a análise psicológica antes de continuar.")
        return

    historia_usuario = progresso["historia_usuario"]
    contexto_livros = progresso["contexto_livros"]
    perfil_investimento = progresso["perfil_investimento"]
    niveis_completos = progresso["niveis_completos"]
    checklist = progresso["checklist"]

    # Identificar o perfil de investimento
    st.write("Identificando seu perfil de investimento...")
    st.subheader("Perfil de Investimento:")
    st.write(perfil_investimento)

    # Gerar metas para o próximo nível
    if niveis_completos not in checklist:
        metas_sugeridas = sugerir_metas(perfil_investimento, historia_usuario)
        checklist[niveis_completos] = [meta.strip() for meta in metas_sugeridas.split("\n") if meta.strip()]
        salvar_progresso(usuario_id, historia_usuario, contexto_livros, perfil_investimento, niveis_completos,
                         checklist)

    # Exibir o checklist do nível atual
    st.subheader(f"Metas do Nível {niveis_completos + 1}")
    nivel_checklist = checklist.get(niveis_completos, [])
    if not nivel_checklist:
        st.warning("Não há metas definidas para este nível. Por favor, tente novamente.")
        return

    checklist_concluido = True
    for i, meta in enumerate(nivel_checklist):
        concluido = st.checkbox(meta, key=f"meta_{niveis_completos}_{i}")
        if not concluido:
            checklist_concluido = False

    # Botão para avançar para o próximo nível
    if checklist_concluido:
        if niveis_completos < 5:  # Verifica se o usuário ainda não atingiu o nível máximo
            if st.button("Avançar para o Próximo Nível"):
                st.success(f"Parabéns! Você concluiu o nível {niveis_completos + 1}.")
                niveis_completos += 1
                salvar_progresso(usuario_id, historia_usuario, contexto_livros, perfil_investimento, niveis_completos,
                             checklist)
                st.rerun()  # Atualiza a página para refletir o novo nível
        else:
            # Exibe um aviso quando o usuário atinge o nível máximo
            st.warning("Você concluiu todos os níveis disponíveis! Para continuar, faça um upgrade no seu plano.")
            st.info("Clique no botão abaixo para saber mais sobre nossos planos premium.")

            # Link para upgrade (exemplo: página de assinatura ou contato)
            st.markdown("[Faça upgrade agora!](https://seuservico.com/upgrade)", unsafe_allow_html=True)
    else:
        st.warning("Você precisa concluir todas as metas antes de avançar para o próximo nível.")

    # Gráfico de progresso
    niveis_totais = 5  # Total de níveis na jornada
    exibir_grafico_progresso(niveis_completos, niveis_totais)

    solicitar_analise_humana(usuario_id, historia_usuario, perfil_investimento)

# Instruções
def pagina_instrucoes():
    st.title("Mezada 1.0 - Instruções")
    st.subheader("Bem-vindo ao Mezada 1.0!")
    st.write("""
    Este aplicativo foi desenvolvido para ajudar você a organizar sua vida financeira, identificar seu perfil de investimento e avançar em uma jornada gamificada de aprendizado financeiro. Abaixo, você encontrará um guia detalhado sobre como usar o aplicativo e suas funcionalidades.

    ### **Como Usar o Aplicativo**

    #### **1. Análise Psicológica Financeira**
    - **O que é?**  
      Esta é a primeira etapa do aplicativo, onde você compartilhará sua história financeira. Com base nela, o sistema identificará se você está enfrentando dificuldades com dívidas ou se está pronto para começar a investir.
    - **Como funciona?**  
      - Insira sua história financeira no campo de texto.
      - Clique no botão "Analisar".
      - O sistema gerará:
        - Um diagnóstico personalizado.
        - Um plano de ação (se necessário).
        - Recomendações baseadas em livros financeiros.

    #### **2. Módulo de Dívidas (Se Aplicável)**
    - **Quando aparece?**  
      Se o sistema detectar que você está enfrentando dificuldades financeiras, você será redirecionado para o módulo de dívidas.
    - **O que fazer?**  
      - Siga o checklist de metas gerado pelo sistema para equilibrar seu orçamento.
      - Conclua todas as metas para avançar para a próxima etapa.

    #### **3. Jornada de Investimento e Gamificação**
    - **O que é?**  
      Após concluir a análise psicológica (e o módulo de dívidas, se aplicável), você entrará na jornada de investimento.
    - **Como funciona?**  
      - A jornada é dividida em 5 níveis.
      - Para cada nível, o sistema sugerirá metas financeiras personalizadas.
      - Conclua todas as metas de um nível para avançar para o próximo.
      - Um gráfico de progresso mostrará seu avanço.

    #### **4. Upgrade de Assinatura**
    - **Por que fazer upgrade?**  
      O plano gratuito oferece acesso aos primeiros 5 níveis. Para desbloquear recursos avançados, como checklists personalizados, suporte prioritário e mentoria individual, você pode fazer upgrade para os planos Basic ou Premium.
    - **Como fazer upgrade?**  
      - Acesse a página "Upgrade de Assinatura" no menu lateral.
      - Escolha o plano que melhor atende às suas necessidades.
      - Siga as instruções para finalizar a assinatura.

    #### **5. Solicitar Análise Humana**
    - **Quando usar?**  
      Se precisar de ajuda especializada, você pode solicitar uma análise humana diretamente via WhatsApp.
    - **Como funciona?**  
      - Clique no botão "Solicitar Análise Humana".
      - Um link será gerado com seus dados para facilitar a comunicação com o consultor.

    ### **Dicas Importantes**
    - **Seja honesto na análise psicológica:** Isso garantirá recomendações mais precisas.
    - **Conclua todas as metas:** Isso é essencial para avançar na jornada.
    - **Explore todos os recursos:** Desde o checklist até o gráfico de progresso, tudo foi projetado para ajudá-lo.

    Estamos aqui para ajudar você a alcançar seus objetivos financeiros. Boa sorte na sua jornada!
    """)



# Função para exibir a página de upgrade de assinatura
def pagina_upgrade_assinatura():
    st.title("Upgrade de Assinatura Mezada 1.0")

    # Layout em colunas para os planos
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Plano Free")
        st.write("- Acesso aos primeiros 5 níveis.")
        st.write("- Checklist básico.")
        st.write("- Sem suporte prioritário.")
        st.write("- Ideal para iniciantes.")
        if st.button("Continuar com Free", key="free"):
            st.info("Você já está no plano Free!")

    with col2:
        st.subheader("Plano Basic")
        st.write("- Acesso a todos os níveis.")
        st.write("- Checklist avançado.")
        st.write("- Suporte padrão por e-mail.")
        st.write("- Relatórios mensais.")
        if st.button("Assinar Basic", key="basic"):
            st.success("Parabéns! Seu plano foi atualizado com sucesso.")
            # Aqui você pode adicionar a lógica para redirecionar para uma nova página, se necessário
            # st.markdown("[Clique aqui para acessar seu novo plano](https://seuservico.com/assinatura-basic)", unsafe_allow_html=True)

    with col3:
        st.subheader("Plano Premium")
        st.write("- Acesso ilimitado a todos os recursos.")
        st.write("- Checklist personalizado.")
        st.write("- Suporte prioritário 24/7.")
        st.write("- Mentoria individual.")
        st.write("- Relatórios detalhados semanais.")
        if st.button("Assinar Premium", key="premium"):
            st.success("Parabéns! Seu plano foi atualizado com sucesso.")
            # Aqui você pode adicionar a lógica para redirecionar para uma nova página, se necessário
            # st.markdown("[Clique aqui para acessar seu novo plano](https://seuservico.com/assinatura-premium)", unsafe_allow_html=True)
################ Suporte #################
def pagina_suporte():

    # Número do consultor (substitua pelo número real)
    numero_suporte = "+5571991858126"  # Exemplo: +55DDNNNNNNNN

    # Mensagem padrão com os dados do usuário
    mensagem_padrao = (
        f"Olá, sou o usuário  do Aplicativo Mezada 1.0 e gostaria de obter suporte.\n"
    )

    # Codifica a mensagem para ser usada em uma URL
    mensagem_codificada = urllib.parse.quote(mensagem_padrao)

    # Gera o link do WhatsApp
    whatsapp_url = f"https://wa.me/{numero_suporte}?text={mensagem_codificada}"

    # Exibe o link no terminal para depuração
    print(f"Link do WhatsApp gerado: {whatsapp_url}")

    # Exibe o botão para abrir o WhatsApp
    st.markdown(f"[Clique aqui para conversar com o Suporte no WhatsApp]({whatsapp_url})", unsafe_allow_html=True)





####### Inicio do Modulo de criação da Planilha Modelo ###################
def criar_planilha_modelo():
    """Cria um modelo de planilha para o usuário preencher."""
    dados = {
        "Nome Completo": [""],
        "Renda Mensal (R$)": [""],
        "Despesas Fixas (R$)": [""],
        "Despesas Variáveis (R$)": [""],
        "Investimentos Mensais (R$)": [""],
        "Total em Investimentos (R$)": [""],
        "Dívidas Atuais (R$)": [""],
        "Parcelas Mensais (R$)": [""],
        "Objetivo Financeiro": [""],
        "Prazo para Meta (meses)": [""],
        "Tipo de Investidor": [""]
    }

    df = pd.DataFrame(dados)
    df.to_excel("modelo_planilha.xlsx", index=False)


#################################################
def pagina_orcamento():
    #st.title("Mezada 1.0")
    st.title("📊 Mezada 1.0 - Análise Planilha de Orçamento")
    criar_planilha_modelo()

    # Permitir download da planilha modelo
    with open("modelo_planilha.xlsx", "rb") as file:
        btn = st.download_button(
            label="📥 Baixar Planilha Modelo",
            data=file,
            file_name="modelo_planilha.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Upload da planilha preenchida pelo usuário
    uploaded_file = st.file_uploader("📤 Faça o upload da sua planilha preenchida (.xlsx)", type=["xlsx"])

    if uploaded_file:
        df_usuario = pd.read_excel(uploaded_file)
        st.write("✅ Planilha carregada com sucesso! Aqui estão seus dados:")
        st.dataframe(df_usuario)

        # Aqui podemos processar os dados e alimentar o modelo de ML
        # Por exemplo, podemos calcular o percentual de gastos e investimentos
        df_usuario["% Investido"] = df_usuario["Investimentos Mensais (R$)"] / df_usuario["Renda Mensal (R$)"] * 100
        df_usuario["% Dívida"] = df_usuario["Dívidas Atuais (R$)"] / df_usuario["Renda Mensal (R$)"] * 100

        st.write("📊 **Análise dos seus dados financeiros:**")
        st.write(df_usuario[["Nome Completo", "% Investido", "% Dívida"]])

        st.write("- *** EM BREVE MAIS FUNCIONALIDADES  DE ANÁLISE!! *** - ")




################################################
# Opção para solicitar análise humana via WhatsApp
def solicitar_analise_humana(usuario_id, historia_usuario, perfil_investimento):
    st.subheader("Solicitar Análise Humana")

    # Verifica se os dados estão sendo recebidos corretamente
    print(f"Usuario ID: {usuario_id}")
    print(f"História do Usuário: {historia_usuario}")
    print(f"Perfil de Investimento: {perfil_investimento}")

    if not usuario_id or not historia_usuario or not perfil_investimento:
        st.error("Erro: Dados do usuário incompletos. Não é possível gerar o link.")
        return

    # Número do consultor (substitua pelo número real)
    numero_consultor = "+5571991858126"  # Exemplo: +55DDNNNNNNNN

    # Mensagem padrão com os dados do usuário
    mensagem_padrao = (
        f"Olá, sou o usuário {usuario_id} e gostaria de uma análise humana.\n"
        f"Minha história: {historia_usuario}\n"
        f"Meu perfil de investimento: {perfil_investimento}."
    )

    # Codifica a mensagem para ser usada em uma URL
    mensagem_codificada = urllib.parse.quote(mensagem_padrao)

    # Gera o link do WhatsApp
    whatsapp_url = f"https://wa.me/{numero_consultor}?text={mensagem_codificada}"

    # Exibe o link no terminal para depuração
    print(f"Link do WhatsApp gerado: {whatsapp_url}")

    # Exibe o botão para abrir o WhatsApp
    st.markdown(f"[Clique aqui para conversar com um consultor no WhatsApp]({whatsapp_url})", unsafe_allow_html=True)

#####################
def pagina_sair():
    # Exibe a interface principal após o login
    # if st.button("Sair"):
    pagina_instrucoes()
    #st.session_state.autenticado = False
    #st.session_state.usuario = None
    #st.session_state.tela_registro = False  # Garante que volta para a tela de login
    #st.rerun()  # Reinicia o aplicativo
    
    


def pagina_jornada_sair_dividas():
    # st.title("Mezada 1.0")
    st.title("📊 **Mezada 1.0 - Em desenvolvimento!**")




##########################################################



# Função principal para integrar tudo
def main():

    st.sidebar.title("Menu")
    opcao = st.sidebar.radio("Escolha uma opção:", ["Instruções","Análise de Perfil", "Jornada de Investimento",
                                                    "Jornada Sair das Dividas","Planilha de Orçamento", "Suporte","Upgrade de Assinatura", "Sair"])

    if opcao == "Instruções":
        pagina_instrucoes()
    elif opcao == "Análise de Perfil":
        pagina_analise_psicologica()
    elif opcao == "Jornada de Investimento":
        pagina_jornada_investimento()
    elif opcao == "Jornada Sair das Dividas":
        pagina_jornada_sair_dividas()
    elif opcao == "Upgrade de Assinatura":
        pagina_upgrade_assinatura()
    elif opcao == "Planilha de Orçamento":
        pagina_orcamento()
    elif opcao == "Suporte":
        pagina_suporte()
    elif opcao == "Sair":
        pagina_sair()


# Inicializa o estado da sessão
#if "autenticado" not in st.session_state:
#    st.session_state.autenticado = False

# Verifica se o usuário está autenticado
#if not st.session_state.autenticado:
#    login3.login3()  # Chama a função de login
#else:

# Executa a aplicação
if __name__ == "__main__":
    inicializar_banco_dados_usuarios()
    main()



# Executa a aplicação
#if __name__ == "__main__":
#    inicializar_banco_dados_usuarios()
#    print("Banco de dados e tabela 'usuarios' criados com sucesso!")
#main()












