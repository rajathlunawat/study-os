# StudyOS

AI-Powered Study Operating System for Students.

Upload lecture notes, syllabi, and previous year question papers. StudyOS parses your documents, builds a searchable knowledge base, and provides AI-powered tutoring through a NotebookLM-style interface.

## Architecture

| Layer | Technology |
|---|---|
| Frontend | Next.js (React, TypeScript) |
| Backend | FastAPI (Python) |
| Database | SQLite |
| Vector Search | FAISS |
| Embeddings | sentence-transformers |
| ML Prediction | scikit-learn (GradientBoosting) |
| PDF Parsing | PyMuPDF |

## Deployment

### Frontend (Vercel)
1. Connect this repo to [Vercel](https://vercel.com).
2. Set root directory to `frontend`.
3. Add environment variable: `NEXT_PUBLIC_API_URL` = your backend URL.

### Backend (Render)
1. Connect this repo to [Render](https://render.com).
2. Set root directory to `backend`.
3. It will auto-detect the `Dockerfile`.

## Local Development

```bash
# Run both servers
.\start.bat
```

## License
MIT
