

def tokenize(message):
    message = message.lower()
    all_words = re.findall("[a-z0-9']+",message)
    return set(all_words)

def count_words(training_set):
    counts = defaultdict(lambda: [0,0])
    for message, is_spam in training_set:
        for word in tokenize(message):
            counts[word][0 if is_spam else 1] += 1
    return counts

def word_probabilities(counts, total_spams, total_non_spams, k=0.5):
    return [(w,
            (spam + k) / (total_spams + 2 * k),
            (non_spam + k) / (total_non_spams + 2 * k))
            for w, (spam, non_spam) in counts.iteritems()]

def spam_probability(word_probs, message):
    message_words = tokenize(message)
    log_prob_if_spam = log_prob_if_not_spam = 0.0
    

    for word, prob_if_spam, prob_if_not_spam in word_probs:
        

        if word in message_words:
            log_prob_if_spam += math.log(prob_if_spam)
            log_prob_if_not_spam += math.log(prob_if_not_spam)


        else:

            log_prob_if_spam += math.log(1.0 - prob_if_spam)
            log_prob_if_not_spam += math.log(1.0 - prob_if_not_spam)

            
    prob_if_spam = math.exp(log_prob_if_spam)
    prob_if_not_spam = math.exp(log_prob_if_not_spam)
    return prob_if_spam / (prob_if_spam + prob_if_not_spam)        


class NaiveBayesClassifier:
    
    def __init__(self, k=0.5):
        self.k = k
        self.word_probs = []

    def train(self, training_set):
        
        num_spams = len([is_spam for message, is_spam in training_set if is_spam]
        num_non_spams = len(training_set) - num_spams


        word_counts = count_words(training_set)

        self.word_probs = word_probabilities(word_counts, num_spams, num_non_spams,self.k)
        
    
   def classify(self, message):
       return spam_probability(self.word_probs, message)


def main():
    path = "home/spam/*/*"
    data = []

    for fn in glob.glob(path):
        is_spam = "ham" not in fn

        with open(fn, 'r') as file:
            for line in file:
                if line.startswith("Subject:"):
                    subject = re.sub(r"^Subject: ", "",line).strip()
                    data.append((subject, is_spam))


   
            
    ranom.seed(0)
    train_data, test_data = split_data(data, 0.75)
    
    classifier = NavieBayesClassifier()
    calssifier.train(train_data)

    classified = [(subject, is_spam, classifier.classify(subject))
                  for subject,is_spam in test_data]

    counts = Counter((is_spam, spam_probability > 0.5)
                     for _, is_spam, spam_probability in classified)
    

    classified.sort(key=lambda row: row[2])

    spammiest_hams = filter(lambda row: not row[1], classified)[-5:]

    hammiest_spams = filter(lambda row: row[1], classified)[:5]
