\# AI Disclosure



\## AI Assistance Used



AI-assisted development tools were used during the development of this project.



AI assistance was used for:



\- Software development and code generation

\- Debugging and troubleshooting

\- Test-case generation and refinement

\- RAG pipeline implementation assistance

\- API integration assistance

\- Documentation drafting

\- Frontend/backend integration assistance



\## Human Review



All AI-assisted output was reviewed and integrated by the project team.



The team tested the application locally, verified the RAG pipeline, checked document retrieval and grounding behavior, tested unsupported questions, verified document indexing/re-indexing/deletion, and reviewed the final implementation.



\## AI Technologies



The project integrates Google Gemini as the language model for answer generation.



The project also uses a Sentence Transformer model for semantic embeddings.



\## Responsible Use



The system is designed to generate answers from an approved enterprise knowledge base. When relevant information cannot be retrieved from the knowledge base, the application is designed to reject unsupported questions rather than intentionally invent information.



\## Secrets



No API keys or other credentials are included in the Git repository. Secrets are stored locally through environment variables and excluded using `.gitignore`.

