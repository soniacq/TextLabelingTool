import pkg_resources
import string
import numpy as np
from dateutil.parser import parse
import json
from ._comm_api import setup_comm_api
from collections import defaultdict
import copy
import random

import pandas as pd
import nltk
import string
import spacy
import json
from spacy import displacy




import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import f1_score
from IPython import display
from matplotlib import pyplot as plt
from modAL.models import ActiveLearner, Committee

RANDOM_STATE_SEED = 0
np.random.seed(RANDOM_STATE_SEED)




top_words=10

global_processed_data = {}

exported_texts = {}

X_seed, y_seed = [], []
X_validation, y_validation = [], []
X_unlabeled, y_unlabeled = [], []
learner = None
performance_history = []

# y_axis could be:
# - freq_total
# - difference
# - freq_abs_pos
# - freq_abs_neg

# enum Yaxis {
#   BYBOTH = 'Top words',
#   BYDIFFERENCE = 'Top words based on the differences',
#   BYPOSITIVE = 'Top words in positive category',
#   BYNEGATIVE = 'Top words in negative category',
# }

def update_yaxis(y_axis):
    sorted_data = sort_words_and_entities(global_processed_data, top_words, y_axis)
    data_dict = prepare_data(sorted_data)
    return data_dict
def comm_get_yaxis_values(msg):
    selected_yaxis = msg['selected_yaxis']
    if (selected_yaxis == "Top words"):
        return {"updated_data": update_yaxis('freq_total')}
    if (selected_yaxis == "Top words based on the differences"):
        return {"updated_data": update_yaxis('difference')}
    if (selected_yaxis == "Top words in positive category"):
        return {"updated_data": update_yaxis('freq_abs_pos')}
    if (selected_yaxis == "Top words in negative category"):
        return {"updated_data": update_yaxis('freq_abs_neg')}
    return {"updated_data": update_yaxis('freq_total')}
setup_comm_api('get_yaxis_values_comm_api', comm_get_yaxis_values)


def comm_get_text(msg):
    id = msg['id']
    category = msg['category']
    if (category == 'positive'):
        return {"text": global_processed_data['raw_texts']['positive_texts'][id]}
    # then it belongs to the negative category
    else:
        return {"text": global_processed_data['raw_texts']['negative_texts'][id]}
setup_comm_api('get_text_comm_api', comm_get_text)

def comm_export_all_texts(msg):
    global exported_texts
    indices = msg['ids']
    category = msg['category']
    text_info = {}
    if (category == 'positive'):
        text_info['texts'] = np.take(global_processed_data['raw_texts']['positive_texts'], indices)
    # then it belongs to the negative category
    else:
        text_info['texts'] = np.take(global_processed_data['raw_texts']['negative_texts'], indices)
    text_info['category'] = category
    text_info['word'] = msg['word']
    exported_texts = text_info
    return {"message": "Exported successfully."}
setup_comm_api('export_all_texts_comm_api', comm_export_all_texts)

def get_exported_texts():
    global exported_texts
    return exported_texts

def id_generator(size=15):
    """Helper function to generate random div ids. This is useful for embedding
    HTML into ipython notebooks."""
    chars = list(string.ascii_uppercase)
    return ''.join(np.random.choice(chars, size, replace=True))


def make_html(data_dict, id):
    lib_path = pkg_resources.resource_filename(__name__, "build/textLabelingTool.js")
    bundle = open(lib_path, "r", encoding="utf8").read()
    html_all = """
    <html>
    <head>
    </head>
    <body>
        <script>
        {bundle}
        </script>
        <div id="{id}">
        </div>
        <script>
            textLabelingTool.renderProfilerViewBundle("#{id}", {data_dict});
        </script>
    </body>
    </html>
    """.format(bundle=bundle, id=id, data_dict=json.dumps(data_dict))
    return html_all

def getSample(text):
    lines = text.split('\n')
    result = []
    for line in lines:
        if line is not '':
            row = line.split(',')
            result.append(row)
    return result


def get_words_frequency(texts, label=None):
    if label:
        print('Analyzing %d documents (%s category)' % (len(texts), label))
    else:
        print('Analyzing %d documents' % len(texts))
    stopwords = nltk.corpus.stopwords.words('english')
    all_words = {}
    total_words = 0
    for idx, text in enumerate(texts):
        words = nltk.word_tokenize(text)
        filtered_words = [word for word in words if word.lower() not in stopwords and len(word)>1]
        for filtered_word in filtered_words:
            if filtered_word not in all_words:
                all_words[filtered_word] = {'word': filtered_word, 'freq_abs': 0, 'freq_nor': 0, 'samples': []}

            all_words[filtered_word]['freq_abs'] += 1
            if idx not in all_words[filtered_word]['samples']:
                all_words[filtered_word]['samples'].append(idx)
            total_words += 1

    sorted_frequencies = []
    for word_data in sorted(all_words.values(), key= lambda x:x['freq_abs'], reverse=True):
        word_data['freq_nor'] = round(word_data['freq_abs']/total_words, 5)
        sorted_frequencies.append(word_data)

    return sorted_frequencies


def join_frequencies(positive_words, negative_words):
    positive_frequencies = {w['word']: w for w in positive_words}
    negative_frequencies = {w['word']: w for w in negative_words}
    all_words = {}

    for word in set(list(positive_frequencies.keys()) + list(negative_frequencies.keys())):
        all_words[word] = {'word': word, 'freq_abs_pos': 0, 'freq_nor_pos': 0, 'samples_pos': [],
                           'freq_abs_neg': 0, 'freq_nor_neg': 0, 'samples_neg': []}
        if word in positive_frequencies:
            all_words[word]['freq_abs_pos'] = positive_frequencies[word]['freq_abs']
            all_words[word]['freq_nor_pos'] = positive_frequencies[word]['freq_nor']
            all_words[word]['samples_pos'] = positive_frequencies[word]['samples']
        if word in negative_frequencies:
            all_words[word]['freq_abs_neg'] = negative_frequencies[word]['freq_abs']
            all_words[word]['freq_nor_neg'] = negative_frequencies[word]['freq_nor']
            all_words[word]['samples_neg'] = negative_frequencies[word]['samples']

        all_words[word]['freq_total'] = all_words[word]['freq_abs_pos'] + all_words[word]['freq_abs_neg']
        all_words[word]['difference'] = abs(all_words[word]['freq_abs_pos'] - all_words[word]['freq_abs_neg'])

    return all_words


def get_words (positive_texts, negative_texts, labels):
    positive_words = get_words_frequency(positive_texts, labels['pos'])
    negative_words = get_words_frequency(negative_texts, labels['neg'])
    all_words = join_frequencies(positive_words, negative_words)
    return all_words


def sort_words(all_words, top_words=10, y_axis='freq_total'):
    return sorted(all_words.values(), key= lambda x:x[y_axis], reverse=True)[:top_words]


def get_entities_frequency(texts, label=None):
    nlp = spacy.load('en_core_web_sm')
    if label:
        print('Analyzing %d documents (%s category)' % (len(texts), label))
    else:
        print('Analyzing %d documents' % len(texts))
    alias = {'ORG':'ORGANIZATION', 'LOC':'PLACE', 'GPE':'CITY/COUNTRY', 'NORP':'GROUP', 'FAC':'BUILDING'}
    unique_entities = {}
    for idx, doc in enumerate(nlp.pipe(texts, n_threads=16, batch_size=100)):
        for entity in doc.ents:
            if entity.label_ in {'CARDINAL', 'ORDINAL', 'QUANTITY'}:
                continue
            entity_type = alias.get(entity.label_, entity.label_)
            entity_name = entity.text
            if entity_name in {'Deir Ezzor', 'Daraa', 'Idlib', 'Aleppo'}:
                entity_type = 'CITY/COUNTRY'
            if entity_type not in unique_entities:
                unique_entities[entity_type] = {}
            if entity_name not in unique_entities[entity_type]:
                unique_entities[entity_type][entity_name] = {'word': entity_name, 'freq_abs': 0, 'freq_nor': 0, 'samples': []}

            unique_entities[entity_type][entity_name]['freq_abs'] += 1

            if idx not in unique_entities[entity_type][entity_name]['samples']:
                unique_entities[entity_type][entity_name]['samples'].append(idx)
    for entity_type in unique_entities.keys():
        total_words = sum([x['freq_abs'] for x in unique_entities[entity_type].values()])
        sorted_frequencies = []
        for word_data in sorted(unique_entities[entity_type].values(), key= lambda x:x['freq_abs'], reverse=True):
            word_data['freq_nor'] = round(word_data['freq_abs']/total_words, 5)
            sorted_frequencies.append(word_data)
        unique_entities[entity_type] = sorted_frequencies
    return unique_entities


def get_entities (positive_texts, negative_texts, labels):
    positive_entities = get_entities_frequency(positive_texts, labels['pos'])
    negative_entities = get_entities_frequency(negative_texts, labels['neg'])

    extracted_data = {}
    for entity_type in set(list(positive_entities.keys()) + list(negative_entities.keys())):
        if entity_type not in positive_entities.keys():
            positive_entities[entity_type]={}
        if entity_type not in negative_entities.keys():
            negative_entities[entity_type]={}
        extracted_data[entity_type] = join_frequencies(positive_entities[entity_type], negative_entities[entity_type])
    return extracted_data


def sort_entities(all_entities, top_words=10, y_axis='freq_total'):
    sorted_entities = {}
    for entity_name in all_entities.keys():
        sorted_entities[entity_name] = sorted(all_entities[entity_name].values(), key= lambda x:x[y_axis], reverse=True)[:top_words]
    return sorted_entities


def sort_words_and_entities(data, top_words=10, y_axis='freq_total'):
    sorted_data = {}
    for key in data.keys():
        if key == 'words':
            sorted_data[key] = sort_words(data[key], top_words, y_axis)
        if key == 'entities':
            sorted_data[key] = sort_entities(data[key], top_words, y_axis)
    return sorted_data

def get_words_entities (data=None, category_column='category', text_column='text', positive_label=1, negative_label=0):
    processed_data = {}
    positive_class = data[data[category_column]==positive_label]
    negative_class = data[data[category_column]==negative_label]

    positive_texts = [str(x) for x in positive_class[text_column].tolist()] # list of texts
    negative_texts = [str(x) for x in negative_class[text_column].tolist()] # list of texts

    labels = {'pos': 'positive', 'neg': 'negative'}
    print('Word Frequency:')
    processed_data["words"] =  get_words (positive_texts, negative_texts, labels)
    print('Named Entity Recognition:')
    processed_data["entities"] = get_entities (positive_texts, negative_texts, labels)
    raw_text = {}
    raw_text['positive_texts'] = positive_texts
    raw_text['negative_texts'] = negative_texts
    processed_data["raw_texts"] = raw_text
    return processed_data


def prepare_data(data, enet_alpha=0.001, enet_l1=0.1):
    data = copy.deepcopy(data)
    word_data = data["words"]
    word_data_JSON = []
    entity_data = data["entities"]
    word_data_JSON = []
    entity_data_JSON = []

    for el in word_data:
        row_pos = {
            "word": el["word"],
            "category":"positive",
            "normalized_frequency":el["freq_nor_pos"],
            "frequency":el["freq_abs_pos"],
            "normalized_frequency_diff_pos_neg": abs(el["freq_nor_pos"]-el["freq_nor_neg"]),
            "frequency_diff_pos_neg": abs(el["freq_abs_pos"]-el["freq_abs_neg"]),
            "samples": el["samples_pos"],
            "total_documents": len(el["samples_pos"])
        }
        word_data_JSON.append(row_pos)
        row_neg = {
            "word": el["word"],
            "category":"negative",
            "normalized_frequency":el["freq_nor_neg"],
            "frequency":el["freq_abs_neg"],
            "normalized_frequency_diff_pos_neg": abs(el["freq_nor_pos"]-el["freq_nor_neg"]),
            "frequency_diff_pos_neg": abs(el["freq_abs_pos"]-el["freq_abs_neg"]),
            "samples": el["samples_neg"],
            "total_documents": len(el["samples_neg"])
        }
        word_data_JSON.append(row_neg)

    for key in entity_data.keys():
        if (key == 'ORGANIZATION' or key == 'PERSON' or key == 'CITY/COUNTRY' ):
            for el in data["entities"][key]:
                row_pos = {
                    "entity_type": key,
                    "word": el["word"],
                    "category":"positive",
                    "normalized_frequency":el["freq_nor_pos"],
                    "frequency":el["freq_abs_pos"],
                    "normalized_frequency_diff_pos_neg": abs(el["freq_nor_pos"]-el["freq_nor_neg"]),
                    "frequency_diff_pos_neg": abs(el["freq_abs_pos"]-el["freq_abs_neg"]),
                    "samples": el["samples_pos"],
                    "total_documents": len(el["samples_pos"])

                }
                entity_data_JSON.append(row_pos)
                row_neg = {
                    "entity_type": key,
                    "word": el["word"],
                    "category":"negative",
                    "normalized_frequency":el["freq_nor_neg"],
                    "frequency":el["freq_abs_neg"],
                    "normalized_frequency_diff_pos_neg": abs(el["freq_nor_pos"]-el["freq_nor_neg"]),
                    "frequency_diff_pos_neg": abs(el["freq_abs_pos"]-el["freq_abs_neg"]),
                    "samples": el["samples_neg"],
                    "total_documents": len(el["samples_neg"])
                }
                entity_data_JSON.append(row_neg)
            
    search_results = {
        "id": str(random.randint(0, top_words)),
        "words": word_data_JSON,
        "entities": entity_data_JSON,
    }
    return search_results

def plot_text_summary(data=None, category_column='category', text_column='text', positive_label=1, negative_label=0, words_entities=None):
    from IPython.core.display import display, HTML
    global global_processed_data
    id = id_generator()
    processed_data = {}
    if words_entities is None:
        processed_data = get_words_entities(data,category_column, text_column, positive_label, negative_label)
        global_processed_data = processed_data
    else:
        processed_data = words_entities
        global_processed_data = words_entities
    y_axis='freq_total'
    sorted_data = sort_words_and_entities(processed_data, top_words, y_axis)
    data_dict = prepare_data(sorted_data)
    html_all = make_html(data_dict, id)
    display(HTML(html_all))

def text_info(texts, label):
    dic_texts = []
    for idx, text in enumerate(texts):
        dic_texts.append({'text': text, 'label': label})
    return dic_texts

def get_text_info(positive_texts, negative_texts, labels):
    positive_texts = text_info(positive_texts, labels['pos'])
    negative_texts = text_info(negative_texts, labels['neg'])
    return positive_texts + negative_texts

def get_sample_text(data, category_column, text_column, positive_label, negative_label):
    positive_class = data[data[category_column]==positive_label]
    negative_class = data[data[category_column]==negative_label]

    positive_texts = [str(x) for x in positive_class[text_column].tolist()] # list of texts
    negative_texts = [str(x) for x in negative_class[text_column].tolist()] # list of texts

    labels = {'pos': 'positive', 'neg': 'negative'}

    sample_texts = get_text_info(positive_texts, negative_texts, labels)

    search_results = {
        "id": str(random.randint(0, top_words)),
        "samples": sample_texts,
    }
    return search_results

def create_single_learner(X, y, estimator=None):
    RANDOM_STATE_SEED = 0
    if estimator is None:
        estimator = RandomForestClassifier(random_state=RANDOM_STATE_SEED, n_estimators=100) 
        # n_estimators=100 to avoid warning regarding n_estimators will change from 10 in version 0.20 to 100 in 0.22
        
    pipeline = Pipeline(
                        steps=[
                                ('tfidf', TfidfVectorizer()),
                                ('classifier', estimator),
                            ]
                        )

    return ActiveLearner(estimator=pipeline, X_training=X, y_training=y)

def dataframe_to_nparray(dataset, text_column, label_column):
    X = dataset[text_column].to_numpy().astype('U')
    y = dataset[label_column].to_numpy()

    return X, y

def get_candidates_instances(learner, n_queries=5):
    global X_seed, y_seed, X_validation, y_validation, X_unlabeled, y_unlabeled, performance_history
    # Allow our model to query our unlabeled dataset for the most
    # informative points according to our query strategy (uncertainty sampling).
    sample_texts = []
    for index in range(n_queries):
        display.clear_output(wait=True)
        # instance that the model think has a high label uncertainty
        query_index, query_instance = learner.query(X_unlabeled)
        X_instance = X_unlabeled[query_index].reshape(1, )
        sample_texts.append({'text': X_instance[0], 'label': 'none'})

         # Remove the queried instance from the unlabeled pool.
        X_unlabeled, y_unlabeled = np.delete(X_unlabeled, query_index, axis=0), np.delete(y_unlabeled, query_index)

    search_results = {
        "id": str(random.randint(0, top_words)),
        "samples": sample_texts,
        'performance_history': performance_history,
    }
    return search_results

def teach_learner(labeled_sample_texts):
    global learner, performance_history
    # Allow our model to query our unlabeled dataset for the most
    # informative points according to our query strategy (uncertainty sampling).
    search_results = {}
    # sample_texts = []
    for tex in labeled_sample_texts:
        label = 0
        if(tex['label'] == 'positive'):
            label = 1
        learner.teach(X=[tex['text']], y=[label])
    # Calculate and report our model's accuracy.
    predictions = learner.predict(X_validation)
    score = f1_score(y_validation, predictions)

    # Save our model's performance for plotting.
    performance_history.append(score)
    # Save our model's performance for plotting.
    # performance_history.append(score)
    if (len(X_unlabeled)>1):
        if (len(X_unlabeled)<5):
            search_results = get_candidates_instances(learner, n_queries=len(X_unlabeled))
        else:
            search_results = get_candidates_instances(learner, n_queries=5)
    return search_results

def get_initial_oracle(initial_dataset, unlabeled_dataset, validation_dataset, model=None):
    global performance_history, learner
    global X_seed, y_seed, X_validation, y_validation, X_unlabeled, y_unlabeled
    # tranform to numpy array
    X_seed, y_seed = dataframe_to_nparray(initial_dataset, 'article', 'articleofinterest')
    X_validation, y_validation = dataframe_to_nparray(validation_dataset, 'article', 'articleofinterest')
    X_unlabeled, y_unlabeled = dataframe_to_nparray(unlabeled_dataset, 'article', 'articleofinterest')
    
    # oracle model
    if(model == None):
        learner = create_single_learner(X_seed, y_seed)
    else:
        learner = model
    
    # predict instances from validation dataset
    predictions = learner.predict(X_validation)
    score = f1_score(y_validation, predictions)
    performance_history = [score]
    return learner

def comm_get_candidates(msg):
    global learner
    labeled_data = msg['labeled_data']
    data_dict = teach_learner(labeled_data)
    return {"candidates": data_dict}
setup_comm_api('get_candidates_comm_api', comm_get_candidates)

def plot_guided_labeling(initial_dataset, unlabeled_dataset, validation_dataset, model=None, category_column='category', text_column='text',  positive_label=1, negative_label=0, words_entities=None):
    from IPython.core.display import display, HTML
    global global_processed_data
    id = id_generator()
    learner = get_initial_oracle(initial_dataset, unlabeled_dataset, validation_dataset, model)
    data_dict = get_candidates_instances(learner, n_queries=5)
    html_all = make_html(data_dict, id)
    display(HTML(html_all))

def plot_guided_labeling_html(initial_dataset, unlabeled_dataset, validation_dataset, model=None, category_column='category', text_column='text',  positive_label=1, negative_label=0, words_entities=None):
    from IPython.core.display import display, HTML
    global global_processed_data
    id = id_generator()
    learner = get_initial_oracle(initial_dataset, unlabeled_dataset, validation_dataset, model)
    data_dict = get_candidates_instances(learner, n_queries=5)
    html_all = make_html(data_dict, id)
    return html_all
