from multiprocessing import process
from flask import Flask, request
from flask_cors import CORS
import json
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

queryWeCareAbout = "eventi interessanti nella città di modena nei prossimi giorni. Eventi più importanti.  Eventi per giovani a Modena. Eventi di Modena. Eventi Modena. Feste e concerti e spettacoli a Modena"

def process_content(content, queryOfInterest):
# we will use a simple cosine similarity approach to this problem: https://www.machinelearningplus.com/nlp/cosine-similarity/
# soft cosine would be a better metric, but this is not the place to talk about it

    #let's make content and queryOfInterest case isensitive
    content = content.lower()
    queryOfInterest = queryOfInterest.lower()
    
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
    
    # to keep it very simple, each element should be 1 if present and 0 if not
    df[df > 0] = 1
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
        # delete content from object
        object["content"] = None
        object["contentQuality"] = process_content(content, queryWeCareAbout)[0][1]

    #return success
    return json.dumps({
        "success": object
    })

if __name__ == '__main__':
    app.run(debug=True)