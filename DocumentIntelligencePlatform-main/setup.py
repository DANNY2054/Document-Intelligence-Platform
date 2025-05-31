from setuptools import setup, find_packages

setup(
    name="document-intelligence-platform",
    version="1.0.0",
    description="A Django-based RAG system for intelligent document processing and AI-powered question answering",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/Obiorachibuike/DocumentIntelligencePlatform",
    packages=find_packages(),
    install_requires=[
        "django>=5.2.1",
        "djangorestframework>=3.16.0",
        "django-cors-headers>=4.7.0",
        "PyPDF2>=3.0.1",
        "python-docx>=1.1.2",
        "tiktoken>=0.9.0",
        "openai>=1.57.0",
    ],
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Framework :: Django",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    keywords="django rag ai nlp document-processing openai gpt vector-search",
)