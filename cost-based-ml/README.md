# Cost-based Machine Learning 

So you've built an ML model and evaluated it's performance on a testing dataset? In case of binary classification, the evaluation tells you how many mistakes the model made, i.e. the percentage of false positives and false negatives, and the same stats for the correct behavior of the model, namely, true positives and true negatives. Of course, the fewer the errors, the better, but for any realistic application the percentage of errors is substantial and it is often unclear if the model is worth using. Moreover, if you just look at the total error rate (sum of false positives and false negatives) you may convince yourself that the model is useless. For example, suppose that 90% of the data points belong to class 0 and the rest to class 1, and your model gives 15% total error. This means that if you employ the model you will be making a mistake 15% of the time and if you don't use the model at all (and just assume that all data points belong to class 0) you will be making a mistake only in 10% of cases. Seems like the model is useless in this case, doesn'it?

This, however, is a rather simplistic way of looking the model evaluation. The truth is that the different types of mistakes the model makes have different intrinsic costs associated with them, depending on the domain and application. Frequently, even when the total error looks bad, when costs are taken into account, the end result clearly favors the use of ML.

This project helps you determine if this is the case and also helps you tune the binary classification threshold (aka cutoff) that you need to choose to turn a score 0..1 returned by the model into a class prediction. This code is written to use Amazon Machine Learning service, but in principle can apply to other binary classification ML algorithms.

To understand the approach better, you are encouraged to read the companion blog post here:
* <https://aws.amazon.com/blogs/ai/predicting-customer-churn-with-amazon-machine-learning/> 
and watch the corresponding re:Invent presentation here:
* <https://youtu.be/D04dxTiDO3E>

