"""
test_rag.py — Comprehensive Verification Suite for GARDA-JKN Medical RAG
Milestone M1: Qdrant Vector Database & Clinical Knowledge Retrieval

This script verifies:
1. MedicalKnowledgeBase initialization and connection.
2. Ingestion of clinical guideline rules with structured metadata.
3. Semantic retrieval for distinct clinical conditions (Stroke, STEMI, Diabetes, Upcoding).
4. SearchResultList contract compliance (List[Dict] behavior and formatted str representation).
5. FastLocalHashEmbeddings fallback correctness.
"""

import sys
import os
import unittest
from typing import List, Dict, Any

from app.core.vector_db import (
    MedicalKnowledgeBase,
    SearchResultList,
    FastLocalHashEmbeddings,
)


class TestMedicalRAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 70)
        print("🏥 GARDA-JKN RAG VERIFICATION TEST SUITE (Tahap 3: Vector DB Qdrant)")
        print("=" * 70)
        # Use an isolated test collection in memory to ensure idempotent, deterministic tests
        cls.kb = MedicalKnowledgeBase(
            collection_name="test_garda_medical_rag",
            force_memory=True,
        )
        cls.kb.connect()
        print("✅ Vector database connected in isolated memory test space.")

        # Ingest representative clinical guideline rules
        cls.test_rules = [
            {
                "text": (
                    "Pedoman Nasional Pelayanan Kedokteran (PNPK) Tata Laksana Stroke: "
                    "Terapi trombolisis intravena menggunakan recombinant tissue plasminogen activator (rTPA) "
                    "diberikan pada pasien stroke iskemik akut dengan onset waktu kurang dari 4.5 jam, "
                    "setelah dipastikan tidak ada perdarahan intrakranial melalui CT scan kepala non-kontras. "
                    "Kriteria eksklusi meliputi tekanan darah sistolik > 185 mmHg atau riwayat perdarahan aktif."
                ),
                "metadata": {
                    "source": "PNPK_Tata_Laksana_Stroke_2026.pdf",
                    "disease": "Stroke Iskemik Akut",
                    "icd10": "I63",
                    "rule_type": "Pedoman Klinis Kemenkes",
                    "page": 14,
                }
            },
            {
                "text": (
                    "Pedoman Verifikasi Klaim BPJS Kasus Sindrom Koroner Akut (STEMI): "
                    "Tindakan Percutaneous Coronary Intervention (PCI) primer merupakan strategi reperfusi pilihan "
                    "pada pasien STEMI dengan onset < 12 jam, dengan target waktu door-to-balloon kurang dari 90 menit. "
                    "Klaim PCI wajib melampirkan rekaman EKG pre dan post tindakan serta hasil angiografi koroner. "
                    "Length of stay (LOS) wajar tanpa komplikasi syok adalah 3 hingga 5 hari rawat."
                ),
                "metadata": {
                    "source": "PNPK_Sindrom_Koroner.pdf",
                    "disease": "Sindrom Koroner Akut (STEMI)",
                    "icd10": "I21",
                    "rule_type": "Pedoman Klinis & Verifikasi",
                    "page": 28,
                }
            },
            {
                "text": (
                    "Pedoman Klinis Diabetes Melitus & Tata Laksana Ulkus Kaki Diabetik: "
                    "Pasien diabetes melitus tipe 2 dengan komplikasi ulkus diabetik memerlukan evaluasi vaskular periferal "
                    "dan kontrol glikemik intensif dengan insulin intravena. Tindakan bedah debridement radikal hanya "
                    "diindikasikan jika terdapat jaringan nekrotik luas atau infeksi flegmon/gangren yang mengancam ekstremitas. "
                    "Perawatan luka rutin di bangsal tidak memenuhi syarat koding debridement kamar operasi."
                ),
                "metadata": {
                    "source": "PNPK_Diabetes.pdf",
                    "disease": "Diabetes Melitus Tipe 2",
                    "icd10": "E11.5",
                    "rule_type": "Pedoman Klinis Endokrin",
                    "page": 42,
                }
            },
            {
                "text": (
                    "Aturan INA-CBG dan Deteksi Upcoding Kasus Rawat Inap (Permenkes 16/2019): "
                    "Penetapan Severity Level III (Berat) wajib dibuktikan dengan adanya diagnosis sekunder komplikasi mayor "
                    "yang mengancam jiwa atau kegagalan organ, seperti penggunaan ventilator mekanik terus menerus > 48 jam, "
                    "syok septik dengan vasopresor, atau koma dengan GCS < 8. "
                    "Klaim yang menetapkan Severity Level III tanpa rekam medis pendukung yang valid adalah indikasi FRAUD (Upcoding) "
                    "dan harus diturunkan tarifnya (DOWNGRADED) ke Severity Level I atau II."
                ),
                "metadata": {
                    "source": "Pedoman Standar Severity Level INA-CBG",
                    "disease": "Regulasi Umum & Upcoding",
                    "icd10": "Cross-Diagnosis",
                    "rule_type": "Aturan Anti-Fraud INA-CBG",
                    "page": 1,
                }
            }
        ]

        # Ingest all rules
        for rule in cls.test_rules:
            n = cls.kb.ingest_document(rule["text"], metadata=rule["metadata"])
            assert n > 0, f"Gagal mengindeks: {rule['metadata']['disease']}"

        print(f"✅ Berhasil menyuntikkan {len(cls.test_rules)} aturan klinis ke dalam memori Qdrant.\n")

    def test_01_search_stroke_clinical_rules(self):
        """Uji penarikan aturan medis spesifik untuk Stroke Iskemik & Trombolisis rTPA."""
        query = "Berapa batas waktu pemberian trombolisis rTPA pada pasien stroke iskemik akut?"
        results = self.kb.search_rules(query, top_k=2)

        self.assertIsInstance(results, list, "Hasil pencarian harus berupa list/SearchResultList")
        self.assertGreater(len(results), 0, "Harus mengembalikan minimal 1 referensi")
        
        top_match = results[0]
        self.assertIn("text", top_match, "Dict hasil harus memiliki kunci 'text'")
        self.assertIn("source", top_match, "Dict hasil harus memiliki kunci 'source'")
        self.assertIn("score", top_match, "Dict hasil harus memiliki kunci 'score'")
        self.assertIn("metadata", top_match, "Dict hasil harus memiliki kunci 'metadata'")
        self.assertGreater(top_match["score"], 0.0, "Similarity score harus positif")
        
        # Verify clinical relevance
        text = top_match["text"].lower()
        self.assertTrue(
            "trombolisis" in text or "stroke" in text or "rtpa" in text,
            f"Kutipan teratas harus relevan dengan stroke: {top_match['text'][:150]}"
        )
        print(f"🔍 [Query: Stroke rTPA] -> Ditemukan: {top_match['source']} (Score: {top_match['score']:.4f})")

    def test_02_search_stemi_pci_rules(self):
        """Uji penarikan pedoman intervensi koroner perkutan (PCI) dan waktu door-to-balloon STEMI."""
        query = "Target waktu door to balloon tindakan PCI primer dan batas LOS rawat STEMI"
        results = self.kb.search_rules(query, top_k=2)

        self.assertGreater(len(results), 0)
        top_match = results[0]
        text = top_match["text"].lower()
        self.assertTrue(
            "pci" in text or "stemi" in text or "koroner" in text,
            f"Kutipan teratas harus relevan dengan STEMI/PCI: {top_match['text'][:150]}"
        )
        print(f"🔍 [Query: STEMI PCI] -> Ditemukan: {top_match['source']} (Score: {top_match['score']:.4f})")

    def test_03_search_diabetes_debridement_rules(self):
        """Uji aturan debridement bedah versus perawatan bangsal pada ulkus kaki diabetes."""
        query = "Indikasi tindakan bedah debridement kamar operasi pada ulkus diabetes melitus"
        results = self.kb.search_rules(query, top_k=2)

        self.assertGreater(len(results), 0)
        top_match = results[0]
        self.assertIn("diabetes", top_match["text"].lower())
        print(f"🔍 [Query: Diabetes Debridement] -> Ditemukan: {top_match['source']} (Score: {top_match['score']:.4f})")

    def test_04_search_upcoding_severity_rules(self):
        """Uji aturan deteksi upcoding dan kriteria ventilator pada Severity Level III INA-CBG."""
        query = "Kapan klaim Severity Level III dianggap upcoding dan harus didowngrade?"
        results = self.kb.search_rules(query, top_k=2)

        self.assertGreater(len(results), 0)
        top_match = results[0]
        text = top_match["text"].lower()
        self.assertTrue(
            "severity" in text or "upcoding" in text or "fraud" in text,
            f"Kutipan harus mencakup aturan upcoding: {top_match['text'][:150]}"
        )
        print(f"🔍 [Query: Upcoding Severity III] -> Ditemukan: {top_match['source']} (Score: {top_match['score']:.4f})")

    def test_05_search_result_list_formatting(self):
        """Uji SearchResultList contract: dapat diindeks seperti list dan diformat sebagai teks medis."""
        query = "trombolisis rTPA stroke 4.5 jam"
        results = self.kb.search_rules(query, top_k=2)

        # List behavior
        self.assertTrue(hasattr(results, "__iter__"))
        self.assertTrue(isinstance(results, list))
        self.assertGreater(len(results), 0)
        
        # String representation
        formatted_str = str(results)
        self.assertIn("Referensi 1", formatted_str)
        self.assertIn("Score:", formatted_str)
        
        # Sources extraction
        sources = results.get_sources()
        self.assertIsInstance(sources, list)
        self.assertGreater(len(sources), 0)
        print(f"📋 Formatted citation preview:\n{formatted_str[:220]}...\n")

    def test_06_fast_local_hash_embeddings(self):
        """Uji FastLocalHashEmbeddings fallback berjalan deterministik dan menghasilkan vektor unit-normal."""
        import numpy as np
        fallback = FastLocalHashEmbeddings(dim=1536)
        
        v1 = fallback.embed_query("stroke iskemik akut")
        v2 = fallback.embed_query("stroke iskemik akut")
        v3 = fallback.embed_query("diabetes melitus komplikasi gangren")
        
        self.assertEqual(len(v1), 1536)
        # Deterministic
        self.assertEqual(v1, v2)
        # Unit norm
        norm = np.linalg.norm(v1)
        self.assertAlmostEqual(norm, 1.0, places=3)
        # Semantic separation
        cos_diff = float(np.dot(v1, v3))
        self.assertLess(cos_diff, 0.99)
        print(f"⚡ FastLocalHashEmbeddings fallback test: OK (Dim: {len(v1)}, Norm: {norm:.3f})")

    def test_07_as_text_parameter(self):
        """Uji parameter as_text=True mengembalikan string langsung."""
        query = "indikasi PCI"
        res_str = self.kb.search_rules(query, top_k=1, as_text=True)
        self.assertIsInstance(res_str, str)
        self.assertIn("Referensi 1", res_str)


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMedicalRAGPipeline)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("🎉 SEMUA PENGUJIAN RAG & VECTOR DB QDRANT LULUS SEMPURNA! (Exit 0)")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"❌ TERJADI KEGAGALAN PADA {len(result.failures)} PENGUJIAN!")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
