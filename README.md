# SolSight

Solar panel inspection and health monitoring. Log a panel's electrical readings (and optionally a thermal or visual image), and SolSight works out whether something is wrong with it, how healthy it is, and where its health is heading over the next 90 days.

```
readings + image ──► defect detection ──► health score ──► 30/60/90-day forecast ──► recommendation
                     (CNN / rules)        (MLP / rules)    (Bi-LSTM / trend)
```

## How the analysis works

Every inspection goes through three stages. Each stage uses its neural network **only if trained weights exist in `backend/saved_models/`**; otherwise it falls back to a physics-based method. The API response says which path was used (`analysis_mode`), so an estimate is never presented as a model output.

| Stage | Model | Fallback when no trained weights |
|---|---|---|
| Defect (Normal / Crack / Hotspot / Soiling) | ResNet18-based CNN | Performance ratio + cell temperature + thermal-contrast check on the image |
| Health (Healthy / Warning / Critical, 0–100 score) | MLP on CNN features + readings | Temperature-corrected performance ratio, minus thermal and defect penalties |
| Forecast (30 / 60 / 90 days) | Bi-LSTM on health history | Least-squares trend over real inspection dates; sudden drops treated as events, not trends |

**Current state:** the CNN is trained (see [Model results](#model-results)) and detects cracks in electroluminescence (EL) cell images; the rules still decide Normal vs. Soiling vs. Hotspot when the CNN sees no crack (`analysis_mode.defect = "cnn+rules"`). The MLP and Bi-LSTM are not trained yet and run on their fallbacks.

The physics side assumes readings near peak sun, a temperature coefficient of −0.40 %/°C above 25 °C, and ~0.7 %/year normal ageing. Status bands: Healthy ≥ 75, Warning 50–75, Critical < 50.

## Stack

- **Backend:** FastAPI, Motor (MongoDB), PyTorch
- **Frontend:** React 18, Vite, React Router, Recharts
- **Database:** MongoDB (Atlas or local), or an in-memory mock for demos

## Running it locally

You need Python 3.11, Node 18+, and either a MongoDB connection string or nothing at all (in-memory mode).

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
MONGO_URI=memory               # or mongodb+srv://user:pass@cluster/
MONGO_DB=solsight
```

With `MONGO_URI=memory`, the API starts with four sample panels and ten weeks of history. Nothing is saved between restarts.

There's no login: the app opens straight on the dashboard and everyone using it shares one workspace.

Start the API:

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health (shows DB status and which models are trained)

### Frontend

From the **project root** (that's where `package.json` lives):

```bash
npm install
npm run dev
```

Open http://localhost:5173. To click through the UI with no backend at all, put `VITE_DEMO_MODE=true` in a root `.env`.

### Docker

Starts MongoDB and the API together:

```bash
docker compose up --build
```

Then run the frontend with `npm run dev` as above.

## API

| Method | Path | What it does |
|---|---|---|
| GET | `/panels` | Your panels with their latest status |
| POST | `/panels` | Add a panel |
| GET | `/panels/{id}` | One panel |
| DELETE | `/panels/{id}` | Remove a panel and its inspections |
| GET | `/panels/{id}/history` | All analyzed inspections, oldest first |
| GET | `/panels/{id}/prediction` | Latest forecast and recommendation |
| POST | `/predict-defect` | Upload readings (+ optional image), run the full analysis, save it |
| POST | `/upload-inspection` | Save raw readings without analysis |

## Model results

The CNN was trained on the public [ELPV dataset](https://github.com/zae-bayern/elpv-dataset) (CC BY-NC-SA 4.0): 2,624 electroluminescence images of single solar cells, each rated by experts with a probability of being defective. Cells rated ≥ 0.5 are labelled **Crack**, the rest **Normal**. The data is split 70 / 15 / 15 (train / validation / test), stratified by label and cell type.

ResNet18 pretrained on ImageNet, layers up to `layer3` frozen, class-weighted loss, 8 epochs on CPU; the best epoch is picked on the validation set.

**Held-out test set (398 images the model never saw):**

|  | Predicted Crack | Predicted Normal |
|---|---|---|
| **Actual Crack** (125) | 93 | 32 |
| **Actual Normal** (273) | 13 | 260 |

| | Precision | Recall | F1 |
|---|---|---|---|
| Crack | 0.877 | 0.744 | 0.805 |
| Normal | 0.890 | 0.952 | 0.920 |

**Accuracy: 88.7%.** Full numbers are in `backend/saved_models/cnn_metrics.json`.

Limits worth stating: ELPV has no hotspot or soiling labels, so the CNN only detects cracks; it was trained on EL images, so thermal or ordinary photos are outside what it has learned; and about a quarter of cracked cells are missed (recall 0.744), mostly the ones experts themselves rated as uncertain.

## Training the models

The training scripts are in `backend/ml_training/`. Each one writes its best checkpoint to `backend/saved_models/`, and the API picks it up on the next restart.

To reproduce the CNN above:

```bash
cd backend/ml_training
git clone --depth 1 https://github.com/zae-bayern/elpv-dataset.git data/elpv-dataset
python prepare_elpv.py --src data/elpv-dataset --out data/elpv
python train_cnn.py --data-dir data/elpv --epochs 8
python evaluate_cnn.py --data-dir data/elpv            # confusion matrix on the test split
```

The MLP and Bi-LSTM need their own labelled data:

```bash
python train_mlp.py --csv data/mlp_features.csv
python train_bilstm.py --csv data/health_history.csv   # columns: panel_id, date, health_score
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

The tests run against the in-memory database. They cover the full inspection flow, upload validation, panel management, and the diagnostics logic.

## Project layout

```
backend/
  app/
    main.py                  FastAPI app, CORS, startup
    db/                      Mongo connection + Pydantic schemas
    routers/                 panels, inspections
    deps.py                  shared-workspace owner (no login)
    services/
      prediction_service.py  runs the 3-stage pipeline
      diagnostics.py         physics/rule-based fallback + recommendations
    models/                  CNN, MLP, Bi-LSTM, VAE definitions
    demo_data.py             sample fleet for in-memory mode
  ml_training/               training scripts
  saved_models/              trained weights (.pt) + cnn_metrics.json
  tests/
frontend/
  api/client.js              API calls (+ offline demo mode)
  src/pages/                 Dashboard, PanelDetail
  src/components/            gauge, chart, upload form, cards
```
