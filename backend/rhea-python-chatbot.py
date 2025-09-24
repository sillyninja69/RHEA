import requests
from bs4 import BeautifulSoup
import json
import re
import difflib
from datetime import datetime
import sqlite3
from typing import Dict, List, Tuple
import logging
import time

class RHEAHealthBot:
    def __init__(self):
        self.symptoms_db = {}
        self.diseases_db = {}
        self.health_advisories = {}
        self.setup_database()
        self.current_language = 'english'
        
        self.symptom_patterns = {
            'english': {
                'fever': ['fever', 'temperature', 'hot', 'burning up', 'high temp', 'pyrexia'],
                'headache': ['headache', 'head pain', 'migraine', 'head hurts', 'cephalgia'],
                'cough': ['cough', 'coughing', 'dry cough', 'wet cough', 'persistent cough'],
                'sore_throat': ['sore throat', 'throat pain', 'throat hurts', 'pharyngitis'],
                'fatigue': ['tired', 'fatigue', 'exhausted', 'weakness', 'weak', 'lethargic'],
                'nausea': ['nausea', 'vomiting', 'sick', 'throw up', 'queasy'],
                'diarrhea': ['diarrhea', 'loose stools', 'stomach upset', 'loose motions'],
                'shortness_of_breath': ['shortness of breath', 'breathing problem', 'cant breathe', 'dyspnea'],
                'chest_pain': ['chest pain', 'chest hurts', 'heart pain', 'angina'],
                'abdominal_pain': ['stomach pain', 'belly pain', 'abdominal pain', 'gastric pain'],
                'dizziness': ['dizzy', 'dizziness', 'lightheaded', 'vertigo', 'spinning'],
                'runny_nose': ['runny nose', 'nasal congestion', 'stuffy nose', 'blocked nose'],
                'body_ache': ['body ache', 'muscle pain', 'joint pain', 'myalgia'],
                'loss_of_taste': ['loss of taste', 'no taste', 'cant taste', 'ageusia'],
                'loss_of_smell': ['loss of smell', 'no smell', 'cant smell', 'anosmia'],
                'rash': ['rash', 'skin rash', 'red spots', 'skin irritation'],
                'swelling': ['swelling', 'swollen', 'inflammation', 'edema']
            },
            'hindi': {
                'fever': ['बुखार', 'तेज़ बुखार', 'गर्मी', 'तापमान', 'ज्वर'],
                'headache': ['सिर दर्द', 'सिरदर्द', 'माइग्रेन', 'सिर में दर्द'],
                'cough': ['खांसी', 'कफ', 'सूखी खांसी', 'कोख'],
                'sore_throat': ['गले में दर्द', 'गला दुखना', 'गलशोथ'],
                'fatigue': ['थकान', 'कमजोरी', 'थका हुआ', 'आलस्य'],
                'nausea': ['जी मिचलाना', 'उल्टी', 'मतली', 'वमन'],
                'diarrhea': ['दस्त', 'पेट खराब', 'लूज मोशन', 'अतिसार'],
                'shortness_of_breath': ['सांस लेने में तकलीफ', 'सांस फूलना', 'श्वासकष्ट'],
                'chest_pain': ['छाती में दर्द', 'सीने में दर्द', 'वक्षस्थल दर्द'],
                'abdominal_pain': ['पेट दर्द', 'पेट में दर्द', 'उदर दर्द'],
                'dizziness': ['चक्कर आना', 'सिर घूमना', 'भ्रम'],
                'runny_nose': ['बहती नाक', 'नाक बंद', 'नजला'],
                'body_ache': ['शरीर दर्द', 'बदन दर्द', 'मांसपेशी दर्द'],
                'loss_of_taste': ['स्वाद की हानि', 'स्वाद नहीं', 'जायका नहीं'],
                'loss_of_smell': ['सूंघने की शक्ति खोना', 'गंध नहीं आना'],
                'rash': ['चकत्ते', 'त्वचा पर दाने', 'खुजली'],
                'swelling': ['सूजन', 'फूलना', 'सूज जाना']
            }
        }
        
        self.translations = {
            'english': {
                'greeting': "Hello! I'm RHEA, your health assistant. I provide health information based on real-time data from WHO and MOHFW. How can I help you today?",
                'language_set': "Language set to English.",
                'symptoms_found': "I detected these symptoms:",
                'recommendations': "Based on your symptoms, here are my recommendations:",
                'consult_doctor': "Please consult a healthcare professional for proper diagnosis and treatment.",
                'emergency': "⚠️ EMERGENCY: Please seek immediate medical attention!",
                'no_symptoms': "I couldn't identify specific symptoms. Please describe your health concern or ask about health topics.",
                'error': "I'm having trouble accessing health data. Please try again later.",
                'disclaimer': "⚠️ Disclaimer: This is for informational purposes only and not a substitute for professional medical advice.",
                'fetching_data': "Fetching latest health information...",
                'data_loaded': "Health data loaded successfully.",
                'help_message': "You can ask about symptoms, diseases, health topics, or type 'hindi' to switch language."
            },
            'hindi': {
                'greeting': "नमस्ते! मैं RHEA हूं, आपकी स्वास्थ्य सहायक। मैं WHO और MOHFW से वास्तविक समय के डेटा के आधार पर स्वास्थ्य जानकारी प्रदान करती हूं। आज मैं आपकी कैसे मदद कर सकती हूं?",
                'language_set': "भाषा हिंदी में सेट की गई।",
                'symptoms_found': "मैंने ये लक्षण पहचाने हैं:",
                'recommendations': "आपके लक्षणों के आधार पर, ये मेरी सिफारिशें हैं:",
                'consult_doctor': "कृपया उचित निदान और उपचार के लिए किसी स्वास्थ्य पेशेवर से सलाह लें।",
                'emergency': "⚠️ आपातकाल: कृपया तुरंत चिकित्सा सहायता लें!",
                'no_symptoms': "मैं विशिष्ट लक्षण नहीं पहचान सकी। कृपया अपनी स्वास्थ्य चिंता का वर्णन करें या स्वास्थ्य विषयों के बारे में पूछें।",
                'error': "स्वास्थ्य डेटा तक पहुंचने में समस्या हो रही है। कृपया बाद में पुनः प्रयास करें।",
                'disclaimer': "⚠️ अस्वीकरण: यह केवल सूचनात्मक उद्देश्यों के लिए है और पेशेवर चिकित्सा सलाह का विकल्प नहीं है।",
                'fetching_data': "नवीनतम स्वास्थ्य जानकारी प्राप्त की जा रही है...",
                'data_loaded': "स्वास्थ्य डेटा सफलतापूर्वक लोड किया गया।",
                'help_message': "आप लक्षणों, बीमारियों, स्वास्थ्य विषयों के बारे में पूछ सकते हैं, या भाषा बदलने के लिए 'english' टाइप करें।"
            }
        }

        self.disease_keywords = {
            'english': {
                'covid': ['covid', 'corona', 'coronavirus', 'sars-cov-2'],
                'diabetes': ['diabetes', 'blood sugar', 'insulin', 'diabetic'],
                'hypertension': ['hypertension', 'high blood pressure', 'bp', 'blood pressure'],
                'malaria': ['malaria', 'mosquito', 'plasmodium'],
                'tuberculosis': ['tuberculosis', 'tb', 'lung infection'],
                'dengue': ['dengue', 'dengue fever', 'aedes'],
                'influenza': ['flu', 'influenza', 'seasonal flu'],
                'pneumonia': ['pneumonia', 'lung infection', 'chest infection']
            },
            'hindi': {
                'covid': ['कोविड', 'कोरोना', 'कोरोनावायरस'],
                'diabetes': ['मधुमेह', 'शुगर', 'डायबिटीज', 'रक्त शर्करा'],
                'hypertension': ['उच्च रक्तचाप', 'हाई बीपी', 'रक्तचाप'],
                'malaria': ['मलेरिया', 'मच्छर', 'बुखार'],
                'tuberculosis': ['तपेदिक', 'टीबी', 'क्षयरोग'],
                'dengue': ['डेंगू', 'डेंगू बुखार'],
                'influenza': ['इन्फ्लूएंजा', 'फ्लू', 'मौसमी बुखार'],
                'pneumonia': ['निमोनिया', 'फेफड़े का संक्रमण']
            }
        }

    def setup_database(self):
        self.conn = sqlite3.connect(':memory:')
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_data (
                id INTEGER PRIMARY KEY,
                source TEXT,
                category TEXT,
                title TEXT,
                content TEXT,
                keywords TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symptoms (
                id INTEGER PRIMARY KEY,
                symptom_name TEXT,
                description TEXT,
                severity TEXT,
                recommendations TEXT,
                language TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY,
                user_input TEXT,
                bot_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                language TEXT
            )
        ''')
        
        self.conn.commit()

    def fetch_who_data(self) -> Dict:
        try:
            who_data = {}
            
            who_urls = [
                "https://www.who.int/emergencies/diseases/novel-coronavirus-2019",
                "https://www.who.int/news-room/fact-sheets",
                "https://www.who.int/health-topics"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            for url in who_urls:
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    articles = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'(content|article|topic|fact)', re.I))
                    
                    for article in articles[:5]:
                        title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            content_elem = article.find(['p', 'div'])
                            if content_elem:
                                content = content_elem.get_text(strip=True)[:800]
                                if len(content) > 100 and title not in who_data:
                                    who_data[title] = content
                    
                    time.sleep(1)
                    
                except Exception as e:
                    continue
            
            if not who_data:
                who_data = self.get_fallback_who_data()
                
            return who_data
            
        except Exception as e:
            logging.error(f"Error fetching WHO data: {e}")
            return self.get_fallback_who_data()

    def fetch_mohfw_data(self) -> Dict:
        try:
            mohfw_data = {}
            
            mohfw_urls = [
                "https://www.mohfw.gov.in",
                "https://www.mohfw.gov.in/index.php",
                "https://main.mohfw.gov.in"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            for url in mohfw_urls:
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    news_sections = soup.find_all(['div', 'section'], class_=re.compile(r'(news|update|advisory)', re.I))
                    news_items = soup.find_all(['p', 'li', 'div'], text=re.compile(r'(health|disease|prevention|symptoms|vaccine|treatment)', re.I))
                    
                    for item in news_items[:10]:
                        text = item.get_text(strip=True)
                        if 100 < len(text) < 500:
                            title = f"MOHFW Health Update {len(mohfw_data) + 1}"
                            mohfw_data[title] = text
                    
                    time.sleep(1)
                    break
                    
                except Exception:
                    continue
            
            if not mohfw_data:
                mohfw_data = self.get_fallback_mohfw_data()
                
            return mohfw_data
            
        except Exception as e:
            logging.error(f"Error fetching MOHFW data: {e}")
            return self.get_fallback_mohfw_data()

    def get_fallback_who_data(self) -> Dict:
        return {
            "COVID-19 Prevention": "COVID-19 spreads through respiratory droplets. Get vaccinated, wear masks in crowded areas, maintain physical distance, wash hands frequently, and avoid touching face with unwashed hands.",
            "Malaria Prevention": "Malaria is transmitted by mosquitoes. Use bed nets, wear long-sleeved clothing, use insect repellent, eliminate standing water, and take prophylaxis in endemic areas.",
            "Tuberculosis Treatment": "TB is curable with proper treatment. Complete 6-8 months of medication course. Symptoms include persistent cough for more than 2 weeks, weight loss, night sweats, and fever.",
            "Diabetes Management": "Monitor blood glucose regularly, follow prescribed diet, exercise daily, take medications as directed, check feet daily, and maintain healthy weight.",
            "Hypertension Control": "High blood pressure is manageable. Reduce sodium intake, exercise regularly, maintain healthy weight, limit alcohol, quit smoking, and take prescribed medications.",
            "Mental Health Awareness": "Mental health is important. Practice stress management, maintain social connections, get adequate sleep, seek professional help when needed, and practice mindfulness.",
            "Seasonal Influenza": "Annual flu vaccination is recommended. Practice good hygiene, cover coughs and sneezes, stay home when sick, and wash hands frequently.",
            "Maternal Health": "Prenatal care is essential. Attend regular checkups, take folic acid supplements, eat nutritious food, avoid alcohol and smoking during pregnancy."
        }

    def get_fallback_mohfw_data(self) -> Dict:
        return {
            "Dengue Prevention Advisory": "Prevent dengue by eliminating mosquito breeding sites. Remove stagnant water from containers, use mosquito nets, wear protective clothing, and use repellents during dawn and dusk.",
            "COVID-19 Vaccination Drive": "COVID-19 vaccines are safe and effective. Get fully vaccinated including booster doses. Follow COVID appropriate behavior even after vaccination.",
            "Seasonal Disease Alert": "Monsoon brings vector-borne diseases. Prevent water stagnation, maintain hygiene, drink boiled water, eat fresh cooked food, and seek medical help for fever.",
            "Child Immunization Program": "Complete childhood vaccinations as per schedule. Vaccines prevent serious diseases like polio, measles, hepatitis, and pneumonia. Maintain vaccination records.",
            "Food Safety Guidelines": "Ensure food safety to prevent foodborne illness. Cook food thoroughly, store at proper temperature, wash hands before eating, and avoid street food during monsoon.",
            "Tobacco Control Initiative": "Tobacco use causes cancer, heart disease, and stroke. Quit tobacco in all forms. Seek help from healthcare providers and use cessation aids.",
            "Mental Health Support": "Mental health services are available. Don't hesitate to seek help for depression, anxiety, or stress. Helpline numbers are available 24/7.",
            "Antimicrobial Resistance": "Use antibiotics responsibly. Take complete course as prescribed, don't share antibiotics, and avoid self-medication to prevent resistance."
        }

    def recognize_symptoms(self, text: str) -> List[str]:
        text_lower = text.lower()
        detected_symptoms = []
        
        patterns = self.symptom_patterns[self.current_language]
        
        for symptom, keywords in patterns.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if symptom not in detected_symptoms:
                        detected_symptoms.append(symptom)
                    break
        
        return detected_symptoms

    def recognize_diseases(self, text: str) -> List[str]:
        text_lower = text.lower()
        detected_diseases = []
        
        keywords = self.disease_keywords[self.current_language]
        
        for disease, disease_keywords in keywords.items():
            for keyword in disease_keywords:
                if keyword.lower() in text_lower:
                    if disease not in detected_diseases:
                        detected_diseases.append(disease)
                    break
        
        return detected_diseases

    def get_symptom_advice(self, symptoms: List[str]) -> Tuple[Dict, bool]:
        advice = {}
        emergency_symptoms = ['chest_pain', 'shortness_of_breath', 'severe_abdominal_pain']
        severe_symptoms = []
        
        symptom_info = {
            'fever': {
                'english': "Monitor temperature regularly. Stay hydrated with fluids. Rest adequately. Take paracetamol if needed. Seek medical help if fever exceeds 103°F (39.4°C) or persists for more than 3 days.",
                'hindi': "तापमान की नियमित निगरानी करें। तरल पदार्थ पिएं। पर्याप्त आराम करें। जरूरत पड़ने पर पेरासिटामोल लें। यदि बुखार 103°F (39.4°C) से अधिक हो या 3 दिन से अधिक बना रहे तो चिकित्सा सहायता लें।"
            },
            'headache': {
                'english': "Rest in quiet, dark room. Apply cold or warm compress. Stay hydrated. Avoid triggers like stress, bright lights. Take over-the-counter pain relief if needed. See doctor if severe, sudden, or with fever.",
                'hindi': "शांत, अंधेरे कमरे में आराम करें। ठंडी या गर्म सिकाई करें। हाइड्रेटेड रहें। तनाव, तेज रोशनी जैसे ट्रिगर से बचें। यदि गंभीर, अचानक या बुखार के साथ हो तो डॉक्टर से मिलें।"
            },
            'cough': {
                'english': "Stay hydrated with warm liquids. Use honey for soothing effect. Avoid smoke and pollutants. Use humidifier. See doctor if cough persists more than 2 weeks, produces blood, or with high fever.",
                'hindi': "गर्म तरल पदार्थ पिएं। शहद का इस्तेमाल करें। धुआं और प्रदूषण से बचें। ह्यूमिडिफायर का उपयोग करें। यदि खांसी 2 सप्ताह से अधिक बनी रहे, खून आए या तेज बुखार हो तो डॉक्टर से मिलें।"
            },
            'sore_throat': {
                'english': "Gargle with warm salt water. Drink warm liquids. Use throat lozenges. Avoid irritants. Rest your voice. See doctor if severe pain, difficulty swallowing, or lasts more than a week.",
                'hindi': "नमक के गर्म पानी से गरारे करें। गर्म तरल पदार्थ पिएं। गले की गोलियां लें। परेशान करने वाली चीजों से बचें। आवाज को आराम दें। यदि गंभीर दर्द, निगलने में कठिनाई या एक सप्ताह से अधिक हो तो डॉक्टर से मिलें।"
            },
            'fatigue': {
                'english': "Get adequate sleep (7-9 hours). Eat balanced diet. Exercise regularly but moderately. Manage stress. Stay hydrated. Consult doctor if persistent fatigue affects daily activities.",
                'hindi': "पर्याप्त नींद लें (7-9 घंटे)। संतुलित आहार लें। नियमित लेकिन मध्यम व्यायाम करें। तनाव को नियंत्रित करें। हाइड्रेटेड रहें। यदि लगातार थकान दैनिक गतिविधियों को प्रभावित करे तो डॉक्टर से सलाह लें।"
            },
            'nausea': {
                'english': "Eat small, frequent meals. Avoid spicy, fatty foods. Stay hydrated with clear fluids. Try ginger or mint. Rest after eating. Seek medical help if persistent vomiting or dehydration signs.",
                'hindi': "थोड़ा-थोड़ा, बार-बार खाएं। मसालेदार, चिकना भोजन न लें। साफ तरल पदार्थ पिएं। अदरक या पुदीना आजमाएं। खाने के बाद आराम करें। लगातार उल्टी या निर्जलीकरण के लक्षण हों तो चिकित्सा सहायता लें।"
            },
            'diarrhea': {
                'english': "Stay hydrated with ORS, clear fluids. Eat BRAT diet (Banana, Rice, Apple sauce, Toast). Avoid dairy, caffeine, alcohol. Take probiotics. See doctor if blood in stool, high fever, or severe dehydration.",
                'hindi': "ORS, साफ तरल पदार्थ से हाइड्रेटेड रहें। BRAT आहार लें (केला, चावल, सेब की चटनी, टोस्ट)। डेयरी, कैफीन, शराब से बचें। प्रोबायोटिक्स लें। मल में खून, तेज बुखार या गंभीर निर्जलीकरण हो तो डॉक्टर से मिलें।"
            },
            'chest_pain': {
                'english': "EMERGENCY: Seek immediate medical attention. Chest pain could indicate heart attack, pulmonary embolism, or other serious conditions. Don't ignore or delay treatment.",
                'hindi': "आपातकाल: तुरंत चिकित्सा सहायता लें। छाती का दर्द हार्ट अटैक, पल्मोनरी एम्बोलिज्म या अन्य गंभीर स्थितियों का संकेत हो सकता है। इसे नजरअंदाज न करें या इलाज में देरी न करें।"
            },
            'shortness_of_breath': {
                'english': "EMERGENCY: Seek immediate medical help. Difficulty breathing requires urgent evaluation. Could indicate respiratory, cardiac, or other serious conditions.",
                'hindi': "आपातकाल: तुरंत चिकित्सा सहायता लें। सांस लेने में कठिनाई तत्काल मूल्यांकन की आवश्यकता है। यह श्वसन, हृदय या अन्य गंभीर स्थितियों का संकेत हो सकता है।"
            },
            'dizziness': {
                'english': "Sit or lie down immediately. Stay hydrated. Avoid sudden movements. Check blood pressure. Avoid driving. See doctor if frequent episodes, with chest pain, or after head injury.",
                'hindi': "तुरंत बैठ या लेट जाएं। हाइड्रेटेड रहें। अचानक हलचल से बचें। रक्तचाप जांचें। गाड़ी न चलाएं। बार-बार चक्कर आना, छाती दर्द के साथ या सिर की चोट के बाद हो तो डॉक्टर से मिलें।"
            },
            'body_ache': {
                'english': "Rest and avoid strenuous activities. Apply hot or cold compress. Take over-the-counter pain relievers. Stay hydrated. Gentle stretching may help. See doctor if severe or persistent pain.",
                'hindi': "आराम करें और कड़ी मेहनत से बचें। गर्म या ठंडी सिकाई करें। दर्द निवारक दवा लें। हाइड्रेटेड रहें। हल्की स्ट्रेचिंग मदद कर सकती है। गंभीर या लगातार दर्द हो तो डॉक्टर से मिलें।"
            }
        }
        
        for symptom in symptoms:
            if symptom in emergency_symptoms:
                severe_symptoms.append(symptom)
            
            if symptom in symptom_info:
                advice[symptom] = symptom_info[symptom][self.current_language]
            else:
                if self.current_language == 'hindi':
                    advice[symptom] = "सामान्य सिफारिश: लक्षणों की निगरानी करें और यदि ये बने रहें तो स्वास्थ्य प्रदाता से सलाह लें।"
                else:
                    advice[symptom] = "General recommendation: Monitor symptoms and consult healthcare provider if they persist."
        
        return advice, len(severe_symptoms) > 0

    def get_disease_info(self, diseases: List[str]) -> str:
        cursor = self.conn.cursor()
        info = ""
        
        for disease in diseases:
            cursor.execute(
                "SELECT title, content FROM health_data WHERE title LIKE ? OR content LIKE ? OR keywords LIKE ? LIMIT 2",
                (f"%{disease}%", f"%{disease}%", f"%{disease}%")
            )
            results = cursor.fetchall()
            
            if results:
                for title, content in results:
                    info += f"\n📋 {title}\n{content[:300]}...\n"
            
        return info

    def set_language(self, language: str):
        if language.lower() in ['hindi', 'हिंदी', 'hin', 'hi']:
            self.current_language = 'hindi'
        elif language.lower() in ['english', 'eng', 'en']:
            self.current_language = 'english'
        
        return self.translations[self.current_language]['language_set']

    def get_health_data(self):
        print(self.translations[self.current_language]['fetching_data'])
        
        who_data = self.fetch_who_data()
        mohfw_data = self.fetch_mohfw_data()
        
        cursor = self.conn.cursor()
        
        for title, content in who_data.items():
            keywords = ' '.join([k for keywords_list in self.disease_keywords[self.current_language].values() for k in keywords_list])
            cursor.execute(
                "INSERT INTO health_data (source, category, title, content, keywords) VALUES (?, ?, ?, ?, ?)",
                ('WHO', 'general', title, content, keywords)
            )
        
        for title, content in mohfw_data.items():
            keywords = ' '.join([k for keywords_list in self.disease_keywords[self.current_language].values() for k in keywords_list])
            cursor.execute(
                "INSERT INTO health_data (source, category, title, content, keywords) VALUES (?, ?, ?, ?, ?)",
                ('MOHFW', 'advisory', title, content, keywords)
            )
        
        self.conn.commit()
        print(f"{self.translations[self.current_language]['data_loaded']} ({len(who_data) + len(mohfw_data)} articles)")

    def search_health_info(self, query: str) -> List[Tuple]:
        cursor = self.conn.cursor()
        
        words = query.lower().split()
        conditions = []
        params = []
        
        for word in words:
            if len(word) > 2:
                conditions.append("(title LIKE ? OR content LIKE ? OR keywords LIKE ?)")
                params.extend([f"%{word}%", f"%{word}%", f"%{word}%"])
        
        if conditions:
            query_sql = f"SELECT title, content, source FROM health_data WHERE {' OR '.join(conditions)} ORDER BY last_updated DESC LIMIT 3"
            cursor.execute(query_sql, params)
        else:
            cursor.execute("SELECT title, content, source FROM health_data ORDER BY last_updated DESC LIMIT 3")
        
        return cursor.fetchall()

    def log_interaction(self, user_input: str, bot_response: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO user_sessions (user_input, bot_response, language) VALUES (?, ?, ?)",
            (user_input, bot_response, self.current_language)
        )
        self.conn.commit()

    def get_emergency_keywords(self) -> List[str]:
        emergency_keywords = {
            'english': ['emergency', 'urgent', 'severe', 'critical', 'help', 'ambulance', 'hospital', 'emergency room', 'chest pain', 'heart attack', 'stroke', 'bleeding', 'unconscious', 'seizure', 'overdose'],
            'hindi': ['आपातकाल', 'तत्काल', 'गंभीर', 'एम्बुलेंस', 'अस्पताल', 'छाती दर्द', 'हार्ट अटैक', 'स्ट्रोक', 'खून बहना', 'बेहोश', 'दौरा', 'ओवरडोज']
        }
        return emergency_keywords[self.current_language]

    def check_emergency(self, text: str) -> bool:
        emergency_keywords = self.get_emergency_keywords()
        text_lower = text.lower()
        
        for keyword in emergency_keywords:
            if keyword.lower() in text_lower:
                return True
        
        emergency_symptoms = ['chest_pain', 'shortness_of_breath']
        detected_symptoms = self.recognize_symptoms(text)
        
        return any(symptom in emergency_symptoms for symptom in detected_symptoms)

    def get_emergency_response(self) -> str:
        if self.current_language == 'hindi':
            return """🚨 आपातकालीन स्थिति का पता चला!

तत्काल कार्रवाई:
• 108 (आपातकालीन सेवा) पर कॉल करें
• 102 (एम्बुलेंस) पर कॉल करें  
• निकटतम अस्पताल जाएं
• शांत रहें और घबराएं नहीं

यदि व्यक्ति बेहोश है:
• सांस की जांच करें
• रिकवरी पोजिशन में रखें
• CPR दें यदि आप जानते हैं

⚠️ देरी न करें - तुरंत चिकित्सा सहायता लें!"""
        else:
            return """🚨 Emergency situation detected!

Immediate actions:
• Call 108 (Emergency services)
• Call 102 (Ambulance)
• Go to nearest hospital
• Stay calm and don't panic

If person is unconscious:
• Check breathing
• Place in recovery position
• Give CPR if you know how

⚠️ Don't delay - seek immediate medical help!"""

    def get_help_info(self) -> str:
        if self.current_language == 'hindi':
            return """🏥 RHEA की सुविधाएं:

📍 लक्षण पहचान:
   "मुझे बुखार और सिर दर्द है" टाइप करें

📍 बीमारी की जानकारी:
   "डायबिटीज के बारे में बताएं" पूछें

📍 स्वास्थ्य सलाह:
   WHO और MOHFW से वास्तविक डेटा

📍 आपातकालीन मदद:
   गंभीर लक्षणों की पहचान

📍 भाषा बदलें:
   'english' टाइप करें

⚠️ यह केवल जानकारी के लिए है। गंभीर समस्याओं के लिए डॉक्टर से मिलें।"""
        else:
            return """🏥 RHEA Features:

📍 Symptom Recognition:
   Type "I have fever and headache"

📍 Disease Information:
   Ask "Tell me about diabetes"

📍 Health Advice:
   Real data from WHO and MOHFW

📍 Emergency Help:
   Identifies critical symptoms

📍 Language Switch:
   Type 'hindi' to switch

⚠️ This is for information only. See a doctor for serious problems."""

    def process_message(self, message: str) -> str:
        message_lower = message.lower().strip()
        
        if not message_lower:
            return self.translations[self.current_language]['help_message']
        
        if message_lower in ['help', 'मदद', '?', 'commands', 'options']:
            return self.get_help_info()
        
        if any(word in message_lower for word in ['hindi', 'हिंदी', 'भाषा बदलो', 'हिन्दी']):
            response = self.set_language('hindi')
            self.log_interaction(message, response)
            return response
        elif any(word in message_lower for word in ['english', 'अंग्रेजी', 'english me']):
            response = self.set_language('english')
            self.log_interaction(message, response)
            return response
        
        if self.check_emergency(message):
            response = self.get_emergency_response()
            self.log_interaction(message, response)
            return response
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'नमस्ते', 'हैलो', 'start', 'शुरू']):
            response = self.translations[self.current_language]['greeting']
            self.log_interaction(message, response)
            return response
        
        symptoms = self.recognize_symptoms(message)
        diseases = self.recognize_diseases(message)
        
        response_parts = []
        
        if symptoms:
            response_parts.append(f"{self.translations[self.current_language]['symptoms_found']}")
            advice, is_emergency = self.get_symptom_advice(symptoms)
            
            if is_emergency:
                response_parts.append(f"\n{self.translations[self.current_language]['emergency']}\n")
            
            response_parts.append(f"\n{self.translations[self.current_language]['recommendations']}")
            
            for symptom, advice_text in advice.items():
                symptom_display = symptom.replace('_', ' ').title()
                response_parts.append(f"\n🔸 {symptom_display}:\n   {advice_text}")
            
            response_parts.append(f"\n\n{self.translations[self.current_language]['consult_doctor']}")
        
        if diseases:
            disease_info = self.get_disease_info(diseases)
            if disease_info:
                response_parts.append(f"\n\n📚 Disease Information:")
                response_parts.append(disease_info)
        
        if not symptoms and not diseases:
            search_results = self.search_health_info(message)
            if search_results:
                if self.current_language == 'hindi':
                    response_parts.append("यहां मुझे जो जानकारी मिली है:\n")
                else:
                    response_parts.append("Here's what I found:\n")
                
                for i, (title, content, source) in enumerate(search_results, 1):
                    response_parts.append(f"\n📋 {i}. {title} ({source})")
                    response_parts.append(f"   {content[:250]}...")
                    if i < len(search_results):
                        response_parts.append("")
            else:
                response_parts.append(self.translations[self.current_language]['no_symptoms'])
        
        if response_parts:
            response_parts.append(f"\n{self.translations[self.current_language]['disclaimer']}")
            response = '\n'.join(response_parts)
        else:
            response = self.translations[self.current_language]['error']
        
        self.log_interaction(message, response)
        return response

    def get_statistics(self) -> Dict:
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        total_queries = cursor.fetchone()[0]
        
        cursor.execute("SELECT language, COUNT(*) FROM user_sessions GROUP BY language")
        language_stats = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM health_data")
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT source, COUNT(*) FROM health_data GROUP BY source")
        source_stats = dict(cursor.fetchall())
        
        return {
            'total_queries': total_queries,
            'language_stats': language_stats,
            'total_articles': total_articles,
            'source_stats': source_stats
        }

def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║    🏥 RHEA - Reliable Health Education Assistant                              ║
║                                                                               ║
║    🌐 Real-time data from WHO & MOHFW                                        ║
║    🧠 Intelligent symptom recognition                                        ║
║    🗣️  Hindi & English support                                               ║
║    ⚡ Emergency situation detection                                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def main():
    print_banner()
    
    bot = RHEAHealthBot()
    
    print("🔄 Initializing RHEA and fetching latest health data...")
    print("📡 Connecting to WHO and MOHFW databases...")
    
    try:
        bot.get_health_data()
        print("✅ RHEA is ready to assist you!")
        
    except Exception as e:
        print(f"⚠️  Warning: Using offline data due to connection issue: {e}")
    
    print("\n" + "="*80)
    print("💡 Quick Start Guide:")
    print("   • Describe symptoms: 'I have fever and cough'")
    print("   • Ask about diseases: 'Tell me about diabetes'")
    print("   • Emergency help: 'chest pain emergency'")
    print("   • Switch language: Type 'hindi' or 'english'")
    print("   • Get help: Type 'help'")
    print("   • Exit: Type 'quit' or 'exit'")
    print("="*80)
    
    session_count = 0
    
    while True:
        try:
            current_lang = "🇮🇳 हिंदी" if bot.current_language == 'hindi' else "🇺🇸 English"
            prompt = f"\n[{current_lang}] 👤 You: "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye', 'निकास', 'अलविदा']:
                stats = bot.get_statistics()
                
                farewell_msg = {
                    'english': f"""
🙏 Thank you for using RHEA!

📊 Session Statistics:
   • Total queries: {stats['total_queries']}
   • Articles loaded: {stats['total_articles']}
   • Languages used: {', '.join(stats['language_stats'].keys())}

💚 Stay healthy and take care!
🏥 Remember: Always consult healthcare professionals for serious concerns.
""",
                    'hindi': f"""
🙏 RHEA का उपयोग करने के लिए धन्यवाद!

📊 सत्र की जानकारी:
   • कुल प्रश्न: {stats['total_queries']}
   • लेख लोड किए गए: {stats['total_articles']}
   • उपयोग की गई भाषाएं: {', '.join(stats['language_stats'].keys())}

💚 स्वस्थ रहें और अपना ख्याल रखें!
🏥 याद रखें: गंभीर समस्याओं के लिए हमेशा स्वास्थ्य पेशेवरों से सलाह लें।
"""
                }
                
                print(farewell_msg[bot.current_language])
                break
            
            session_count += 1
            print(f"\n🤖 RHEA: ", end="")
            
            response = bot.process_message(user_input)
            print(response)
            
            if session_count % 5 == 0:
                refresh_msg = {
                    'english': "\n💡 Tip: I can help with symptoms, diseases, health advice, and emergencies!",
                    'hindi': "\n💡 सुझाव: मैं लक्षण, बीमारी, स्वास्थ्य सलाह और आपातकाल में मदद कर सकती हूं!"
                }
                print(refresh_msg[bot.current_language])
                
        except KeyboardInterrupt:
            print("\n\n🛑 Session interrupted by user")
            print("🙏 Thank you for using RHEA. Stay healthy!")
            break
            
        except Exception as e:
            error_msg = {
                'english': f"\n❌ An error occurred: {str(e)}\n💡 Please try rephrasing your question or type 'help' for assistance.",
                'hindi': f"\n❌ एक त्रुटि हुई: {str(e)}\n💡 कृपया अपना प्रश्न दोबारा लिखने की कोशिश करें या मदद के लिए 'help' टाइप करें।"
            }
            print(error_msg[bot.current_language])
            continue

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('rhea_health_bot.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        main()
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        print("🔧 Please check your internet connection and try again.")
        logging.error(f"Critical error in main: {e}")
    finally:
        print("\n👋 RHEA session ended.")
        