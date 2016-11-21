[["java:package:com.br.ice.service"]]
module phone{
	interface PhoneService{
		string uploadPhoneNumber(string priority, string strategy, string phoneNumber, string projectName);
	    string downloadResult(string taskId, string mode, string projectName);
	};      		 
};