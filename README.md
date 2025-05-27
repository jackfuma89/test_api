# 📞 Customer Info API

Questa API, realizzata in Python utilizzando Flask, permette di recuperare informazioni su clienti partendo dal loro numero di telefono, interrogando un database CSV.

## 🚀 Come avviare l'applicazione

### 1. Clona la repository

```bash
git clone <url_repository>
cd <nome_repository>
```

### 2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 3. Configura il CSV

Inserisci il tuo file CSV `nlpearl_test_db.csv` nella cartella principale del progetto. Assicurati che contenga almeno le colonne seguenti:

* `contract_code`
* `phone_number`
* `activation_date`
* `platform`
* `status`
* `average_arpu`
* `service_type`

### 4. Avvia il server

```bash
python app.py
```

L'API sarà disponibile su:

```
http://localhost:8000
```

## 🔥 Utilizzo

### Richiedere informazioni cliente tramite telefono

```http
GET /customer/phone/<numero_di_telefono>
```

#### Esempio di risposta:

```json
{
  "data": {
    "contract_code": "12345678",
    "platform": "Q BLACK",
    "status": "ATTIVO",
    "average_arpu": "50",
    "service_type": "TV",
    "activation_date": "2021-01-01T15:38:01Z"
  }
}
```

### Richiedere campi specifici (opzionale)

```http
GET /customer/phone/<numero_di_telefono>?fields=contract_code,platform,status
```

## 🛠️ Tecnologie usate

* **Python**
* **Flask**
* **Pandas**
* **Flask-CORS**

## 🌐 Deployment

Puoi deployare facilmente l'applicazione usando piattaforme come [Render](https://render.com) o [Heroku](https://heroku.com).

---

📄 **Licenza**: MIT

