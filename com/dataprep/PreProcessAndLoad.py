from lxml import etree
from jproperties import Properties
import pandas as pd
import prestodb

start = 'start'
end = 'end'
all_tree = etree.iterparse("../../resources/dblp.xml", events=(start, end), dtd_validation=True, recover=True)
_, parent = next(all_tree)
start_tag = None

article = 'article'
proceedings = 'proceedings'
inproceedings = 'inproceedings'
article_list = []
inproc_list = []
proc_list = []

configs = Properties()
with open('../../resources/nrdbs.properties', 'rb') as read_prop:
    configs.load(read_prop)

article_attribute = configs.get("journal_article_tags").data
proc_attribute = configs.get("conf_proc_tags").data
inproc_attribute = configs.get("conf_article_tags").data


def create_data(elem):
    item = dict()
    item['key'] = elem.attrib.get('key')
    for ent1 in elem.getchildren():
        if elem.tag == article and ent1.tag in article_attribute:
            item[ent1.tag] = ent1.text
            article_list.append(item)
        if elem.tag == proceedings and ent1.tag in proc_attribute:
            item[ent1.tag] = ent1.text
            proc_list.append(item)
        if elem.tag == inproceedings and ent1.tag in inproc_attribute:
            item[ent1.tag] = ent1.text
            inproc_list.append(item)


for event, tree in all_tree:
    if tree.tag in [article, inproceedings, proceedings]:
        if event == start and start_tag is None:
            start_tag = tree.tag
            create_data(tree)
        if event == end and tree.tag == start_tag:
            start_tag = None
            parent.clear()

dblp = {article: article_list, proceedings: proc_list, inproceedings: inproc_list}

article_df = (pd.DataFrame.from_dict(dblp[article]).dropna()).drop_duplicates()
inproc_df = (pd.DataFrame.from_dict(dblp[inproceedings])).drop_duplicates()
proc_df = (pd.DataFrame.from_dict(dblp[proceedings])).drop_duplicates()

presto_db_conn = prestodb.dbapi.connect(host=configs.get("PRESTO_DB_HOST").data,
                                        port=8080,
                                        http_scheme='https',
                                        catalog='dblp-catalog',
                                        schema=configs.get("PRESTO_DB_SCHEMA").data,
                                        auth=prestodb.auth.BasicAuthentication(configs.get("PRESTO_DB_User").data,
                                                                               configs.get("PRESTO_DB_PWD").data),
                                        verify=False)
cur = presto_db_conn.cursor()
