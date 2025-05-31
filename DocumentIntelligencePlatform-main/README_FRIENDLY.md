I can't "update" the existing Markdown document in your system directly. However, I can provide you with the full content of the Markdown you provided, assuming the emojis you've used are intended to be part of the document.

Here's the Markdown content you supplied:

```markdown
# Document Intelligence Platform

A powerful Django-based RAG (Retrieval-Augmented Generation) system for intelligent document processing and AI-powered question answering.

---

## 📑 Table of Contents
- [Features](#-features)
- [API Endpoints](#-api-endpoints)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Technology Stack](#-technology-stack)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

---

## 📂 Features

### 📄 Document Processing
- **Multi-format Support**: Upload and process TXT, PDF, DOCX, and Markdown files
- **Smart Text Extraction**: Automatic text extraction with page counting
- **Intelligent Chunking**: Advanced text chunking with token overlap for better context

### 🤖 AI-Powered Intelligence
- **OpenAI Integration**: Uses GPT-4o for intelligent question answering
- **Vector Search**: Semantic similarity search using OpenAI embeddings
- **Confidence Scoring**: AI provides confidence levels for answers
- **Source Citations**: Track which document sections support each answer

### 🚀 Production-Ready Backend
- **RESTful API**: Complete REST API for all operations
- **Database Management**: PostgreSQL/SQLite support with proper migrations
- **Error Handling**: Comprehensive error handling and logging
- **Admin Interface**: Django admin for document management

---

## 🔗 API Endpoints

### Documents
- `GET /api/documents/` - List all documents
- `POST /api/documents/upload/` - Upload new document
- `GET /api/documents/{id}/` - Get document details
- `DELETE /api/documents/{id}/delete/` - Delete document

### Querying
- `POST /api/documents/query/` - Ask questions about documents

### Statistics
- `GET /api/vector-store/stats/` - Get system statistics

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API Key

### Installation

1. Clone the repository:
```bash
git clone [https://github.com/Obiorachibuike/DocumentIntelligencePlatform.git](https://github.com/Obiorachibuike/DocumentIntelligencePlatform.git)
cd DocumentIntelligencePlatform
```

2. Install dependencies:
```bash
pip install django djangorestframework django-cors-headers PyPDF2 python-docx tiktoken openai
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the server:
```bash
python manage.py runserver 0.0.0.0:5000
```

---

## 💡 Usage Examples

### Upload a Document
```bash
curl -X POST http://localhost:5000/api/documents/upload/ \
  -F "file_path=@document.pdf" \
  -F "title=My Document"
```

### Ask Questions
```bash
curl -X POST http://localhost:5000/api/documents/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 1,
    "question": "What is the main topic of this document?",
    "num_chunks": 3
  }'
```

---

## 🗂 Project Structure

```
├── documents/              # Main app for document processing
│   ├── models.py           # Document and DocumentChunk models
│   ├── views.py            # API endpoints
│   ├── processing.py       # Text extraction and chunking
│   ├── vector_store.py     # Vector embeddings management
│   ├── llm_service.py      # OpenAI integration
│   └── serializers.py      # API serializers
├── rag_system/             # Django project settings
├── media/                  # Uploaded documents storage
└── manage.py               # Django management script
```

---

## ⚙️ Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `DEBUG`: Set to False in production
- `DJANGO_SECRET_KEY`: Django secret key for production

### Settings
- `CHUNK_SIZE`: Token size per text chunk (default: 500)
- `CHUNK_OVERLAP`: Token overlap between chunks (default: 50)
- `MAX_CHUNKS_FOR_CONTEXT`: Maximum chunks for context (default: 5)

---

## 🛠 Technology Stack

- **Backend**: Django 5.2, Django REST Framework
- **AI/ML**: OpenAI GPT-4o, OpenAI Embeddings
- **Database**: SQLite (development), PostgreSQL (production)
- **Document Processing**: PyPDF2, python-docx, tiktoken
- **Storage**: File-based vector storage with JSON

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🆘 Support

For questions or issues, please open an issue on GitHub or contact the development team.
```

If you were looking to make specific changes or have questions about certain sections, feel free to ask!