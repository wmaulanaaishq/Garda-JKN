import os
import json
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.evaluate import evaluate
from app.agents.workflow import garda_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kita gunakan DeepSeek via AIML API yang sudah ada di .env (OPENAI compatible)
# DeepEval akan otomatis membaca OPENAI_API_KEY jika ada. 
# Mari set secara manual untuk deepeval agar memakai AIML_API_KEY.
os.environ["OPENAI_API_KEY"] = os.environ.get("AIML_API_KEY", "")
os.environ["OPENAI_BASE_URL"] = "https://api.aimlapi.com/v1"

test_claims = [
    {
        "id_kunjungan": "TEST-001",
        "nama_pasien": "Siti Aminah",
        "nik": "3201012345678902",
        "usia": 45,
        "diag_awal": "Demam Typhoid",
        "diag_sekunder_1": "",
        "tindakan_1": "Pemeriksaan Darah",
        "icu_days": 0,
        "severity_level": 1,
        "biaya_tagih": 2500000,
        "durasi_rawat": 3
    }
]

def test_garda_jkn_agent():
    logger.info("Menjalankan klaim simulasi ke GARDA-JKN Workflow (DeepEval)...")
    
    test_cases = []
    
    for claim in test_claims:
        # Input LLM (Question)
        input_query = (f"Evaluasi klaim pasien dengan diagnosis {claim['diag_awal']}. "
                       f"Biaya: Rp {claim['biaya_tagih']}, LOS: {claim['durasi_rawat']} hari.")
        
        initial_state = {"claim_data": claim}
        final_state = garda_app.invoke(initial_state)

        # Output LLM (Answer)
        actual_output = final_state.get("adjudication_reason", "No reason.")
        
        # Retrieval Context (RAG)
        retrieval_context = [final_state.get("rag_context", "")]

        test_case = LLMTestCase(
            input=input_query,
            actual_output=actual_output,
            retrieval_context=retrieval_context
        )
        test_cases.append(test_case)

    # Inisialisasi Metrik (Model evaluasi default adalah GPT-4o, tapi karena base url dan key diubah,
    # ia akan menembak ke AIML API menggunakan deepseek-chat/coder atau model yang kita tentukan).
    # Untuk metrik DeepEval yang gratis dan jalan dengan baik di endpoint OpenAI-compatible:
    answer_relevancy = AnswerRelevancyMetric(threshold=0.7, model="deepseek/deepseek-chat")
    faithfulness = FaithfulnessMetric(threshold=0.7, model="deepseek/deepseek-chat")

    logger.info("Menjalankan evaluasi DeepEval...")
    results = evaluate(test_cases, [answer_relevancy, faithfulness])
    logger.info("Evaluasi selesai.")

if __name__ == "__main__":
    test_garda_jkn_agent()
