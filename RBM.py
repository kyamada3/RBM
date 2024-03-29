import sys
import numpy
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

numpy.seterr(all='ignore')

def sigmoid(x):
    return 1. / (1 + numpy.exp(-x))


class RBM(object):
    def __init__(self, input=None, n_visible=2, n_hidden=3, \
        W=None, hbias=None, vbias=None, numpy_rng=None, initial_n_hidden = 0):
        
        self.n_visible = n_visible  # num of units in visible (input) layer
        self.n_hidden = n_hidden    # num of units in hidden layer

        if numpy_rng is None:
            numpy_rng = numpy.random.RandomState(1234)


        if W is None:
            a = 1. / n_visible
            initial_W = numpy.array(numpy_rng.uniform(  # initialize W uniformly
                low=-a,
                high=a,
                size=(n_visible, n_hidden)))

            W = initial_W
        else:
            for i in range(n_hidden-initial_n_hidden):
            	W = numpy.c_[ W, numpy.zeros(28*28)]

        if hbias is None:
            hbias = numpy.zeros(n_hidden)  # initialize h bias 0
        else:
        	for i in range(n_hidden-initial_n_hidden):
        		hbias = numpy.append(hbias, numpy.zeros(1))

        if vbias is None:
            vbias = numpy.zeros(n_visible)  # initialize v bias 0


        self.numpy_rng = numpy_rng
        self.input = input
        self.W = W
        self.hbias = hbias
        self.vbias = vbias

        # self.params = [self.W, self.hbias, self.vbias]


    def contrastive_divergence(self, lr=0.1, k=1, input=None):
        if input is not None:
            self.input = input
                
        ''' CD-k '''
        ph_mean, ph_sample = self.sample_h_given_v(self.input)

        chain_start = ph_sample

        for step in xrange(k):
            if step == 0:
                nv_means, nv_samples,\
                nh_means, nh_samples = self.gibbs_hvh(chain_start)
            else:
                nv_means, nv_samples,\
                nh_means, nh_samples = self.gibbs_hvh(nh_samples)

        # chain_end = nv_samples


        self.W += lr * (numpy.dot(self.input.T, ph_sample)
                        - numpy.dot(nv_samples.T, nh_means))
        self.vbias += lr * numpy.mean(self.input - nv_samples, axis=0)
        self.hbias += lr * numpy.mean(ph_sample - nh_means, axis=0)

        # cost = self.get_reconstruction_cross_entropy()
        # return cost


    def sample_h_given_v(self, v0_sample):
        h1_mean = self.propup(v0_sample)
        h1_sample = self.numpy_rng.binomial(size=h1_mean.shape,   # discrete: binomial
                                       n=1,
                                       p=h1_mean)

        return [h1_mean, h1_sample]


    def sample_v_given_h(self, h0_sample):
        v1_mean = self.propdown(h0_sample)
        v1_sample = self.numpy_rng.binomial(size=v1_mean.shape,   # discrete: binomial
                                            n=1,
                                            p=v1_mean)
        
        return [v1_mean, v1_sample]

    def propup(self, v):
        pre_sigmoid_activation = numpy.dot(v, self.W) + self.hbias
        return sigmoid(pre_sigmoid_activation)

    def propdown(self, h):
        pre_sigmoid_activation = numpy.dot(h, self.W.T) + self.vbias
        return sigmoid(pre_sigmoid_activation)


    def gibbs_hvh(self, h0_sample):
        v1_mean, v1_sample = self.sample_v_given_h(h0_sample)
        h1_mean, h1_sample = self.sample_h_given_v(v1_sample)

        return [v1_mean, v1_sample,
                h1_mean, h1_sample]
    

    def get_reconstruction_cross_entropy(self):
        pre_sigmoid_activation_h = numpy.dot(self.input, self.W) + self.hbias
        sigmoid_activation_h = sigmoid(pre_sigmoid_activation_h)
        
        pre_sigmoid_activation_v = numpy.dot(sigmoid_activation_h, self.W.T) + self.vbias
        sigmoid_activation_v = sigmoid(pre_sigmoid_activation_v)

        cross_entropy =  - numpy.mean(
            numpy.sum(self.input * numpy.log(sigmoid_activation_v) +
            (1 - self.input) * numpy.log(1 - sigmoid_activation_v),
                      axis=1))
        
        return cross_entropy

    def reconstruct(self, v):
		h = sigmoid(numpy.dot(v, self.W) + self.hbias)
		print >> sys.stderr, h.shape
		reconstructed_v = sigmoid(numpy.dot(h, self.W.T) + self.vbias)
		
		print >> sys.stderr, reconstructed_v[0,]
				
		data2 = numpy.zeros((28,28), dtype=numpy.int)
		k = 0
		for i in range(0, 28):
			for j in range(0, 28):
				data2[i,j] = reconstructed_v[0,k]
				k+=1

		plt.imshow(data2, cmap = 'gray')
		
		plt.show()
		
		return reconstructed_v

def test(learning_rate=0.1, k=1, training_epochs=200):

	rng = numpy.random.RandomState(123)
	training_size = 2	
	data = numpy.zeros((training_size,28*28), dtype=numpy.int)
	data_set = open ("test_images.txt", "r")
	for i in range (0,training_size):
		line_col = 1
		data_col = 0
		temp = 0
		line = data_set.readline()
		while line[line_col-1:line_col] != '\n':
			if (line[line_col-1:line_col] != ' ') & (line[line_col:line_col+1] != ' '):
				temp *= 10
				temp += int(line[line_col-1:line_col])*10
			elif (line[line_col-1:line_col] != ' ') & (temp != 0):
				temp += int(line[line_col-1:line_col])
				data[i,data_col] = temp
				temp = 0
				data_col += 1
			elif line[line_col-1:line_col] != ' ':
				data[i,data_col] = int(line[line_col-1:line_col])
				data_col += 1
			line_col += 1
			
	# construct RBM
	rbm = RBM(input=data, n_visible=28*28, n_hidden=400, numpy_rng=rng)

    # train
	for epoch in xrange(training_epochs):
		rbm.contrastive_divergence(lr=learning_rate, k=k)
		cost = rbm.get_reconstruction_cross_entropy()
		#print >> sys.stderr, 'Training epoch %d, cost is ' % epoch, cost
    	
	rbm = RBM(input=data, n_visible=28*28, n_hidden=784, numpy_rng=rng, W=rbm.W, hbias=rbm.hbias, vbias=rbm.vbias, initial_n_hidden=rbm.n_hidden)
        
	for epoch in xrange(training_epochs):
		rbm.contrastive_divergence(lr=learning_rate, k=k)
		cost = rbm.get_reconstruction_cross_entropy()
		#print >> sys.stderr, 'Training epoch %d, cost is ' % epoch, cost
        
	data_set.close()

	# test
	
#	test_data = numpy.zeros((30,28*28), dtype=numpy.int)
#	test_data_set = open ("test_images.txt", "r")
#	for i in range (0,30):
#		line_col = 1
#		data_col = 0
#		temp = 0
#		line = test_data_set.readline()
#		while line[line_col-1:line_col] != '\n':
#			if (line[line_col-1:line_col] != ' ') & (line[line_col:line_col+1] != ' '):
#				temp *= 10
#				temp += int(line[line_col-1:line_col])*10
#			elif (line[line_col-1:line_col] != ' ') & (temp != 0):
#				temp += int(line[line_col-1:line_col])
#				test_data[i,data_col] = temp
#				temp = 0
#				data_col += 1
#			elif line[line_col-1:line_col] != ' ':
#				test_data[i,data_col] = int(line[line_col-1:line_col])
#				data_col += 1
#			line_col += 1

	data2 = numpy.zeros((28,28), dtype=numpy.int)
	k = 0
	for i in range(0, 28):
		for j in range(0, 28):
			data2[i,j] = data[0,k]
			k+=1

	plt.imshow(data2, cmap = 'gray')
	plt.show()
		
	
	print rbm.reconstruct(data)
	
#	test_data_set.close()
			
#	print data[59999,]
			
if __name__ == "__main__":
	test()
