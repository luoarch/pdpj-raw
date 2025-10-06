# PDPJ Dashboard - Interface Next.js

Interface moderna e responsiva para o PDPJ API Enterprise Edition v2.0, construída com Next.js 15, TypeScript e Tailwind CSS seguindo os princípios do Atomic Design.

## 🚀 Características

- **Next.js 15** com App Router
- **TypeScript** para tipagem estática
- **Tailwind CSS** para styling
- **Atomic Design** para organização de componentes
- **Zustand** para gerenciamento de estado
- **React Query** para cache e sincronização de dados
- **React Hook Form** + **Zod** para formulários
- **Design responsivo** e acessível
- **Tema escuro/claro** automático

## ⭐ NOVOS RECURSOS (v2.0)

- ✅ **Download Assíncrono** - Downloads em background via Celery
- ✅ **Webhooks** - Notificações automáticas quando downloads concluírem
- ✅ **Status em Tempo Real** - Progresso 0-100% com polling automático
- ✅ **Gerenciamento de Downloads** - Página dedicada para acompanhar downloads
- ✅ **Configuração de Webhooks** - Configure URLs de callback no perfil
- ✅ **API Client Completo** - 7 novos endpoints integrados

## 📁 Estrutura do Projeto

```
src/
├── app/                    # App Router (Next.js 15)
│   ├── (protected)/       # Rotas protegidas
│   │   ├── dashboard/     # Dashboard principal
│   │   └── processes/     # Lista de processos
│   ├── login/            # Página de login
│   └── layout.tsx        # Layout raiz
├── components/           # Componentes organizados por Atomic Design
│   ├── atoms/           # Componentes atômicos
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   └── avatar.tsx
│   ├── molecules/       # Componentes moleculares
│   │   ├── search-form.tsx
│   │   ├── process-card.tsx
│   │   └── status-indicator.tsx
│   ├── organisms/       # Organismos
│   │   ├── process-list.tsx
│   │   └── dashboard-stats.tsx
│   ├── layout/          # Componentes de layout
│   └── ui/              # Componentes de UI básicos
├── lib/                 # Utilitários e configurações
│   ├── api-client.ts    # Cliente da API PDPJ
│   └── utils.ts         # Funções utilitárias
├── store/               # Gerenciamento de estado (Zustand)
│   ├── auth-store.ts    # Store de autenticação
│   └── app-store.ts     # Store da aplicação
└── providers/           # Providers React
    └── query-provider.tsx
```

## 🛠️ Instalação e Configuração

### 1. Instalar Dependências

```bash
npm install
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env.local` na raiz do projeto:

```env
# PDPJ API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Development settings
NODE_ENV=development
```

### 3. Executar em Desenvolvimento

```bash
npm run dev
```

A aplicação estará disponível em `http://localhost:3000`

### 4. Build para Produção

```bash
npm run build
npm start
```

## 🔐 Autenticação

A aplicação usa tokens JWT para autenticação. Tokens de demonstração disponíveis:

- **Teste**: `pdpj_test_b3Xd4tVTqsXrKzJ_sIinewIxmsinYTaIf6KFK9XINvM`
- **Admin**: `pdpj_admin_xYl0kmPaK9o00xe_BdhoGBZvALr7YuHKI0gTgePAbZU`

## 📱 Funcionalidades

### Dashboard
- Status do sistema em tempo real
- Métricas de performance
- Status dos serviços (Database, Redis, S3, PDPJ API)
- Informações do sistema

### Processos
- Lista paginada de processos
- Busca avançada com filtros
- Visualização de detalhes
- Download de documentos

### Monitoramento
- Métricas em tempo real
- Health checks
- Performance indicators

## 🎨 Atomic Design

A aplicação segue os princípios do Atomic Design:

### Atoms (Átomos)
Componentes básicos e indivisíveis:
- `Button` - Botões com variantes
- `Input` - Campos de entrada
- `Card` - Containers de conteúdo
- `Badge` - Indicadores de status
- `Avatar` - Imagens de perfil

### Molecules (Moléculas)
Combinações de átomos:
- `SearchForm` - Formulário de busca
- `ProcessCard` - Card de processo
- `StatusIndicator` - Indicador de status

### Organisms (Organismos)
Combinações de moléculas:
- `ProcessList` - Lista de processos
- `DashboardStats` - Estatísticas do dashboard

## 🔧 Tecnologias Utilizadas

- **Next.js 15.5.4** - Framework React
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Framework CSS
- **Zustand** - Gerenciamento de estado
- **React Query** - Cache e sincronização
- **React Hook Form** - Formulários
- **Zod** - Validação de schemas
- **Lucide React** - Ícones
- **date-fns** - Manipulação de datas

## 📊 API Integration

A aplicação integra com todos os 15 endpoints da API PDPJ:

- **Health & Status** (2 endpoints)
- **Authentication** (2 endpoints)
- **Users** (2 endpoints)
- **Processes** (4 endpoints)
- **Documents** (1 endpoint)
- **Monitoring** (4 endpoints)

## 🚀 Deploy

### Vercel (Recomendado)

1. Conecte o repositório ao Vercel
2. Configure as variáveis de ambiente
3. Deploy automático

### Docker

```bash
# Build da imagem
docker build -t pdpj-ui .

# Executar container
docker run -p 3000:3000 pdpj-ui
```

## 📝 Scripts Disponíveis

- `npm run dev` - Servidor de desenvolvimento
- `npm run build` - Build para produção
- `npm run start` - Servidor de produção
- `npm run lint` - Verificação de código
- `npm run type-check` - Verificação de tipos

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT.

---

**Desenvolvido com ❤️ para o PDPJ API Enterprise Edition v2.0**