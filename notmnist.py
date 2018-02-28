from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import tarfile
from IPython.display import display, Image
from scipy import ndimage
from sklearn.linear_model import LogisticRegression
from six.moves.urllib.request import urlretrieve
from six.moves import cPickle as pickle
from six.moves import range
from IPython.display import display, Image



url = 'https://commondatastorage.googleapis.com/books1000/'
last_percent_reported = None
data_root = '.'

def download_progress_hook(count, blockSize, totalSize):

	global last_percent_reported
	percent = int(count * blockSize * 100 / totalSize)

	if last_percent_reported != percent:
		if percent % 5 == 0:
			sys.stdout.write("%s%%" % percent)
			sys.stdout.flush()
		else:
			sys.stdout.write(".")
			sys.stdout.flush()

		last_percent_reported = percent

def maybe_download(filename,expected_bytes, force=False):
	dest_filename = os.path.join(data_root, filename)
	if force or not os.path.exists(dest_filename):
		print('Attempting to download:',filename)
		filename = urlretrieve(url + filename, dest_filename, reporthook=download_progress_hook)
		print('\nDownload Complete')
	statinfo = os.stat(dest_filename)
	if statinfo.st_size == expected_bytes:
		print('Found and verified', dest_filename)
	else:
		raise Exception(
			'Failed to verify ' + dest_filename + '. Can you get it with a browser?' )
	return dest_filename

train_filename = maybe_download('notMNIST_large.tar.gz', 247336696)
test_filename = maybe_download('notMNIST_small.tar.gz', 8458043)


num_classes = 10
np.random.seed(133)

def mabye_extract(filename, force=False):
	root = os.path.splitext(os.path.splitext(filename)[0])[0]
	if os.path.isdir(root) and not force:
		print("%s already present - Skipping extraction of %s. " % (root,filename))
	else:
		print("Extracting data for %s This may take a while. Please wait. " %root)
		tar = tarfile.open(filename)
		sys.stdout.flush()
		tar.extractall(data_root)
		tar.close()
	data_folders = [
		os.path.join(root, d) for d in sorted(os.listdir(root))
		if os.path.isdir(os.path.join(root, d))]
	if len(data_folders) != num_classes:
		raise Exception(
			'Expected %d folders, one per class. Found %d instead.' %(num_classes, len(data_folders)))
	print(data_folders)
	return data_folders

train_folders = mabye_extract(train_filename)
test_folders = mabye_extract(test_filename)

display(Image(filename="notMNIST_small/A/Q0NXaWxkV29yZHMtQm9sZEl0YWxpYy50dGY=.png"))


image_size = 28
pixel_depth = 255.0

def load_letter(folder, min_num_images):
	image_files = os.listdir(folder)
	dataset = np.ndarray(shape=(len(image_files),image_size,image_size),dtype=np.float32)

	print(folder)
	num_images = 0
	for image in image_files:
		image_file = os.path.join(folder,image)
		try:
			image_data = (ndimage.imread(image_file).astype(float) - pixel_depth/2) /pixel_depth
			if image_data.shape != (image_size,image_size):
				raise Exception('Unexpected image shape: %s' % str(image_data.shape))
			dataset[num_images,:, :] = image_data
			num_images = num_images + 1
		except IOError as e:
			print('Could not read:' , image_file, ':', e, '- it\'s ok, skipping.')

	dataset = dataset[0:num_images,:,:]
	if num_images < min_num_images:
		raise Exception('Many fewer images than expected: %d < %d' %(num_images,min_num_images))
	print('Full dataset tensor',dataset.shape)
	print('Mean:',np.mean(dataset))
	print('Standard deviation;',np.std(dataset))
	return dataset


def mabye_pickle(data_folders,min_num_images_per_class, force=False):
	dataset_names = []
	for folder in data_folders:
		set_filename = folder + '.pickle'
		dataset_names.append(set_filename)
		if os.path.exists(set_filename) and not force:
			print('%s already present - Skipping pickling.' % set_filename)
		else:
			print('Pickling %s.' %set_filename)
			dataset = load_letter(folder, min_num_images_per_class)
			try:
				with open(set_filename, 'wb') as f:
					pickle.dump(dataset, f, pickle.HIGHEST_PROTOCOL)
			except Exception as e:
				print('Unable to save data to', set_filename, ':', e)
	return dataset_names

train_datasets = mabye_pickle(train_folders, 45000)
test_datasets = mabye_pickle(test_folders, 1800)

#pickle_file = train_datasets[1]

'''with open(pickle_file,'rb') as f:
	print("hello")
	letter_set = pickle.load(f)
	sample_idx = np.random.randint(len(letter_set))
	sample_image = letter_set[sample_idx,:,:]
	plt.figure()
	plt.imshow(sample_image)
	plt.show()'''


def make_arrays(nb_rows,img_size):
	if nb_rows:
		dataset = np.ndarray((nb_rows, img_size, img_size), dtype=np.float32)
		labels = np.ndarray(nb_rows, dtype=np.int32)
	else:
		dataset,labels = None,None
	return dataset,labels

def merge_datasets(pickle_files, train_size, valid_size=0):
	num_classes = len(pickle_files)
	valid_dataset, valid_labels = make_arrays(valid_size,image_size)
	train_dataset, train_labels = make_arrays(train_size,image_size)
	vsize_per_class = valid_size
	tsize_per_class = train_size

	start_v,start_t = 0,0
	end_v,end_t = vsize_per_class, tsize_per_class
	end_l = vsize_per_class + tsize_per_class
	for label, pickle_file in enumerate(pickle_files):
		try:
			with open(pickle_file, 'rb') as f:
				letter_set = pickle.load(f)

				np.random.shuffle(letter_set)
				if valid_dataset is not None:
					valid_letter = letter_set[:vsize_per_class,:,:]
					valid_dataset[start_v:end_v, :, :] = valid_letter
					valid_labels[start_v:end_v] = label
					start_v += vsize_per_class
					end_v += vsize_per_class

				train_letter = letter_set[vsize_per_class:end_l,:,:]
				train_dataset[start_t:end_t, :, :] = train_letter
				train_labels[start_t:end_t] = labels
				start_t += tsize_per_class
				end_t += tsize_per_class
		except Exception as e:
			print('Unable to process data from',pickle_file,':',e)
			raise
	return valid_dataset, valid_labels, train_dataset, train_labels

train_size = 200000
valid_size = 10000
test_size = 10000

valid_dataset, valid_labels,train_dataset,train_labels = merge_datasets(train_datasets,train_size,valid_size)
_,_,test_dataset,test_labels = merge_datasets(test_datasets,test_size)

print('Training:', train_dataset.shape, train_labels.shape)
print('Validation:',valid_dataset.shape, valid_labels.shape)
print('Testing:',test_dataset.shape,test_labels.shape)

def randomize(dataset, labels):
	permutation = np.random.permutation(labels.shape[0])
	shuffled_dataset = dataset[permutation,:,:]
	shuffled_labels = labels[permutation]
	return shuffled_dataset, shuffled_labels

train_dataset,train_labels = randomize(train_dataset,train_labels)
test_dataset, test_labels = randomize(test_dataset, test_labels)
valid_dataset, valid_labels = randomize(valid_dataset, valid_labels)

pickle_file = 'notMNIST.pickle'
try:
	f = open(pickle_file, 'wb')
	save = {
		'train_dataset': train_dataset,
		'train_labels' : train_labels,
		'valid_dataset' : valid_dataset,
		'valid_labels' : valid_labels,
		'test_dataset' : test_dataset,
		'test_labels' : test_labels,

	}
	pickle.dump(save, f, pickle.HIGHEST_PROTOCOL)
	f.close()
except Exception as e:
	print('Unable to save data to', pickle_file, ':', e)
	raise

statinfo = os.stat(pickle_file)
print('Compressed pickle size:', statinfo.st_size)

#reloading pickle file
'''pickle_file = 'notMNIST.pickle'

with open(pickle_file, 'rb') as f:
	save = pickle.load(f)
	train_dataset = save['train_dataset']
	train_labels = save['train_labels']
	valid_dataset = save['valid_dataset']
	valid_labels = save['valid_labels']
	test_dataset = save['test_dataset']
	test_labels = save['test_labels']
	del save
	print('Training set', train_dataset.shape, train_labels.shape)
	print('Validation set', valid_dataset.shape, valid_labels.shape)
	print('Test set', test_dataset.shape, test_labels.shape)

image_size = 28
num_labels = 10

def reformat(dataset, labels):
	dataset = dataset.reshape((-1, image_size * image_size)).astype(np.float32)

	labels = (np.arrange(num_labels) == labels[:,None]).astype(np.float32)
	return dataset, labels

train_dataset, train_labels = reformat(train_dataset, train_labels)
valid_dataset, valid_labels = reformat(valid_dataset, valid_labels)
test_dataset, test_labels = reformat(test_dataset, test_labels)
print('Training set', train_dataset.shape, train_labels.shape)
print('Validation set', valid_dataset.shape, valid_labels.shape)
print('Test set', test_dataset.shape, test_labels.shape)

#training
train_subset = 1000

graph = tf.Graph()
with graph.as_default():

	tf_train_dataset = tf.constant(train_dataset[:train_subset, :])
	tf_train_labels = tf.constant(train_labels[:train_subset])
	tf_valid_dataset = tf.constant(valid_dataset)
	tf_test_dataset = tf.constant(test_dataset)

	weights = tf.Variable(tf.truncated_normal([image_size* image_size,num_labels]))
	biases = tf.Variable(tf.zeros([num_labels]))

	logits = tf.matmul(tf_train_dataset, weights) + biases
	loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=tf_train_labels,logits=logits))

	optimizer = tf.train.GradientDescentOptimizer(0.5).minimize(loss)

	train_prediction = tf.nn.softmax(logits)
	valid_prediction = tf.nn.softmax(tf.matmul(tf_valid_dataset,weights) + biases)
	test_prediction = tf.nn.softmax(tf.matmul(tf_test_dataset,weights) + biases)

num_steps = 801

def accuracy(predictions, labels):
	return (100.0 * np.sum(np.argmax(predictions, 1) == np.argmax(labels, 1)) / predictions.shape[0])


with tf.Session(graph=graph) as session:
%
	tf.global_variables_initalizer().run()
	print('Initialized')
	for step in range(num_steps):

		_,l, predictions = session.run([optimizer, loss, train_prediction])
		if(step % 100 == 0):
			print('Loss at step %d: %f' % (step, l))
			print('Training accuracy: %.1f%%' % accuracy(predictions, train_labels[:train_subset,:]))

			print('Validation acuracy: %.1f%%' % accuracy(valid_prediction.eval(),valid_labels))

	print('Test accuracy: %.1f%%' %accuracy(test_prediction.eval(),test_labels))'''



