from flask import Flask, request
from flask_cors import CORS
import json
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def process_content(content, queryOfInterest):
# we will use a simple cosine similarity approach to this problem: https://www.machinelearningplus.com/nlp/cosine-similarity/
# soft cosine would be a better metric, but this is not the place to talk about it
    docs = [content, queryOfInterest]
    count_vectorizer = CountVectorizer(stop_words="italian")
    count_vectorizer = CountVectorizer()
    sparse_matrix = count_vectorizer.fit_transform(docs)
    doc_term_matrix = sparse_matrix.todense()
    
    df = pd.DataFrame(
    doc_term_matrix,
    columns=count_vectorizer.get_feature_names_out(),
    index=["content", "queryOfInterest"],
    )
    return cosine_similarity(df, df)

app = Flask(__name__)

CORS(app = app, resources={r"/*": {"origins": ["*"]}})
@app.route('/', methods = ["PUT", "POST"])
def api():
    data = request.get_json()
    object = data["object"]
    # check if content is set
    if "content" in object:
        content = object["content"]
        print(content)
        # delete content from object
        object["content"] = None
        object["contentQuality"] = 0.5

    #return success
    return json.dumps({
        "success": object
    })

if __name__ == '__main__':
    # nltk.download('stopwords')
    # app.run(debug=True)
    content = """
    Il Corso di Laurea in Ingegneria Informatica fornisce una formazione ad ampio spettro, che consente di comprendere le problematiche e le soluzioni dell’informatica applicata a molteplici settori dei servizi e dell’industria.

Le materie di studio sono specifiche dell’Ingegneria Informatica fin dal I anno e tutte prevedono, oltre a lezioni in aula, attività pratiche nei molteplici laboratori attrezzati e corredati di strumenti all’avanguardia e tool gratuiti, che favoriscono la professionalizzazione, la progettualità e il capire “come funziona”, obiettivi primari di qualsiasi ingegnere.

Per ulteriori dettagli, si vedano le slide di presentazione del corso.

I laureati in Ingegneria Informatica trovano solitamente occupazione in aziende informatiche e manifatturiere locali e nazionali; va anche considerata la possibilità di intraprendere professioni di tipo imprenditoriale, che nell’informatica costituiscono una realtà perseguibile con pochi investimenti, molte idee, un computer e una connessione a Internet.

Il Corso di Laurea in Ingegneria Informatica nell’anno accademico 2023-2024 sarà a numero programmato (230 studenti), per entrare in graduatoria è necessario partecipare al bando di accesso disponibile al seguente link.

Al seguente link potete visionare il video sull'accoglienza alle matricole che si è tenuto in data 09/02/2023.

Tutte le informazioni, compreso il Piano degli Studi contenente gli insegnamenti offerti, sono disponibili a questo link:
    """
    queryWeCareAbout = "L'intelligenza artificiale non è banale, anche se in informatica ormai è normale"
    print(process_content(content, queryWeCareAbout))