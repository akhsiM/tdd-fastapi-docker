from newspaper import Article


def generate_summary(url: str)-> str:
    artcile = Article(url)
    article.download()
    article.parse()
    article.nlp()
    return article.summary

