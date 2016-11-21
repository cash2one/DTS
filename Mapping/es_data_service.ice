#ifndef TEST_ICE
#define TEST_ICE

[["java:package:com.br.es_data_service"]]
module api {
	["java:getset"]
	struct KV {
            string k;
            string v;
	};
	["java:type:java.util.ArrayList<String>"]
	sequence<string> set;
	["java:type:java.util.ArrayList<KV>"]
	sequence<KV> kvs;
	interface ESDataServiceInterface {
		idempotent set getAddrData (kvs querys);
		idempotent set getApplyLoanData (set keys);
		idempotent set getBlackListData (set keys);
                idempotent set getContactData (string phone);
                idempotent set getQQData (string qq);
                idempotent set getSubCate3Data (set keys);
                idempotent set getSubClientNewData (set keys);
	};
};

#endif