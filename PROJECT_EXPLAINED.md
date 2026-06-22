# Legal AI Project – Simple Explanation (Hinglish)

## 1) Ye project kya hai?

Ye project ek smart legal contract analyzer hai. Iska kaam yeh hai ki:

- user PDF contract upload karta hai
- system contract ko read karta hai
- clauses (legal clauses) nikalta hai
- unhe standard clauses ke saath compare karta hai
- risky clauses dikhata hai
- AI explanation bhi deta hai

Isse legal team ko contract ko jaldi aur aasaan tarike se samajhne mein help milti hai.

---

## 2) Project ka simple idea

Socho aap ek contract leke aaye ho. Aap chahte ho ki system bataaye:

- kis clause mein risk hai?
- wo approved standard clause se kaise alag hai?
- iski importance kya hai?

Ye project yeh sab karta hai.

---

## 3) Pehle humne kya kiya? Phir kaise integrate kiya?

### Step 1: Backend banaya

Pehle humne backend create kiya jahan se API chalegi.

- Python ka framework use kiya gaya: FastAPI
- Iska matlab hai: frontend se request aayegi, backend usko handle karega aur result return karega.

### Step 2: Database setup kiya

Humne MySQL database use kiya.

- uploaded contract ka record rakha jata hai
- extracted clauses save hote hain
- risk results save hote hain
- final report summary bhi save hota hai

### Step 3: PDF read karna shuru kiya

Contract PDF upload hoti hai, phir system usko read karta hai.

- Tesseract OCR use kiya gaya hai
- unstructured library use kiya gaya hai
- isse PDF ka text nikaala jata hai

### Step 4: Clauses extract kiye

Text ko analyze karke clauses nikalte hain.

- har clause ko alag identify kiya jata hai
- clauses ka content saved hota hai

### Step 5: Risk analysis kiya

Ab system clause ko standard legal clauses ke saath compare karta hai.

- sentence embeddings use kiye gaye
- FAISS vector search use kiya gaya
- Isolation Forest use kiya gaya taaki unusual/risky clauses identify ho sakein

### Step 6: AI explanation di gayi

Risky clauses ke liye AI explanation generate hoti hai.

- Groq LLM use kiya gaya
- har risky clause ke liye short explanation banai jaati hai

### Step 7: Frontend banaya

Frontend React mein banaya gaya.

- upload page
- analyze page
- history page
- contract detail page

### Step 8: Sab kuch integrate kiya

Ab backend aur frontend ko connect kiya gaya.

- frontend PDF upload karta hai
- backend analyze karta hai
- result frontend par dikhaya jata hai
- data database mein save hota hai

---

## 4) Is project ka main workflow (simple flow)

Yeh flow is tarah ka hai:

1. User PDF upload karta hai
2. File backend tak jaati hai
3. Backend file save karta hai
4. PDF ko parse karke text nikalta hai
5. Text se clauses extract hote hain
6. Clauses ko standard clauses se compare kiya jata hai
7. Risk score aur risk level calculate hota hai
8. AI explanation generate hoti hai
9. Results database aur JSON files mein save hote hain
10. Frontend par results show hote hain

---

## 5) Folder structure aur har folder ka matlab

### Root files

- main.py
  - project ka main entry point hai
  - FastAPI app start karta hai

### app/

- app/__init__.py
  - app package ka initial file hai

### app/api/

- app/api/routes.py
  - yahan sab API endpoints define hain
  - upload, analyze, fetch contracts, fetch reports etc.

### app/database/

- app/database/database.py
  - MySQL connection setup karta hai

- app/database/models.py
  - database tables define karta hai

- app/database/crud.py
  - database operations jaise save, fetch, update karne ke functions

### app/models/

- app/models/schemas.py
  - API response models define karta hai

### app/services/

- app/services/parser.py
  - PDF ko read karke text nikalta hai

- app/services/industry_clause_engine.py
  - clauses extract karta hai

- app/services/risk_engine.py
  - clause risk analyze karta hai

- app/services/explainer.py
  - AI explanation generate karta hai

### data/

- data/raw/
  - raw uploaded files ya sample data ke liye

- data/processed/
  - processed JSON outputs save hote hain
  - jaise contract.json, final_contract_analysis.json, etc.

- data/uploads/
  - temporary uploaded PDF files yahan save hoti hain

### legal-ai-frontend/

- React frontend ka complete project hai

---

## 6) Important files aur unka kaam

### main.py

Is file se server start hota hai.

- FastAPI app create hota hai
- CORS enable hota hai
- routes include hote hain
- server run hota hai

### app/api/routes.py

Yeh sabse important backend file hai.

Ismein ye kaam hote hain:

- /health check
- /analyze endpoint
- /contracts endpoint
- /contracts/{id}/results endpoint
- /reports endpoint

### app/services/parser.py

PDF ko parse karta hai.

- PDF text extract karta hai
- output JSON file mein save karta hai

### app/services/industry_clause_engine.py

Contract text se clauses nikalta hai.

- clause list banata hai
- unko processed JSON mein save karta hai

### app/services/risk_engine.py

Yeh clause risk detect karta hai.

- clause ko standard clause se compare karta hai
- similarity score nikalta hai
- anomaly score nikalta hai
- final risk level decide karta hai: HIGH / MEDIUM / LOW

### app/services/explainer.py

Yeh risky clauses ke liye AI-based explanation produce karta hai.

- Groq AI se explanation lekar deta hai
- result ko final JSON mein save karta hai

### app/database/models.py

Yeh database tables define karta hai:

- contracts
- clauses
- risk_results
- analysis_reports

### legal-ai-frontend/src/services/api.js

Frontend aur backend ke beech connection karta hai.

- upload request bhejta hai
- results fetch karta hai

### legal-ai-frontend/src/pages/Analyze.js

Is page par user PDF upload karta hai aur analysis run karta hai.

---

## 7) Project mein kaunse technologies use hue hain?

### Backend

- Python
- FastAPI
- SQLAlchemy
- MySQL
- Pydantic
- Uvicorn

### PDF & Text Processing

- Tesseract OCR
- unstructured

### AI / ML

- SentenceTransformer
- InLegalBERT
- FAISS
- Isolation Forest
- Groq LLM

### Frontend

- React
- React Router
- Axios
- CSS

---

## 8) Iska real use kya hai?

Ye project ka use isliye hota hai:

- contract review karne mein
- risky clauses identify karne mein
- legal compliance check karne mein
- business teams ko quick insights dene mein
- legal document analysis mein automation laane mein

---

## 9) Project ka basic architecture

Yeh simple architecture hai:

User -> React Frontend -> FastAPI Backend -> PDF Parser / Clause Extractor / Risk Engine / AI Explainer -> MySQL + JSON Files -> Frontend Results

---

## 10) Run karne ka simple process

### Backend

1. Python environment activate karo
2. required packages install karo
3. MySQL start karo
4. .env file create karo
5. backend run karo

### Frontend

1. frontend folder mein jao
2. npm install karo
3. npm start karo

### Important setup points

- MySQL database ka naam banana pad sakta hai: legal_ai_db
- DATABASE_URL set karna hota hai
- GROQ_API_KEY set karna hota hai
- Tesseract install hona chahiye

---

## 11) Data kaise save hota hai?

Project do jagah data save karta hai:

### 1. MySQL database

- contract information
- clauses
- risk results
- final summaries

### 2. JSON files

- processed contract text
- industry clauses
- risk analysis output
- final contract analysis output

Isse aap local bhi inspect kar sakte ho.

---

## 12) Is project mein kya strong point hai?

- PDF contract ko analyze kar sakta hai
- AI explanation deta hai
- risk level identify karta hai
- frontend se easy use hota hai
- database mein results save karta hai

---

## 13) Is project mein kya limitations ho sakti hain?

- PDF text extraction imperfect ho sakta hai agar file scanned image ho
- AI explanation based on external API (Groq) par depend karta hai
- standard clause data ka quality important hai
- large documents par processing slow ho sakta hai

---

## 14) Agar aap is project ko samajhna chahte ho to yaad rakho

Project ka simple logic yeh hai:

- upload karo
- read karo
- extract karo
- compare karo
- risk batado
- explanation do

Yeh hi project ka core idea hai.

---

## 15) Ek line mein summary

Ye project ek AI-powered legal contract risk analyzer hai jo PDF contracts ko upload karke unmein risky clauses detect karta hai aur unka simple explanation deta hai.
