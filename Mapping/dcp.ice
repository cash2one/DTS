#ifndef TEST_ICE
#define TEST_ICE

[["java:package:com.br.dcp_data_service_api"]]
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
    interface DCPDataService {
        idempotent kvs neoQuery (string idCard, string cell, string email, string qq, string weibo, int depth);
        idempotent set neoQueryOriginal (string idCard, string cell, string email, string qq, string weibo, int depth);
        idempotent set findQunNumByQQNum (string qqnum);
        idempotent set findAllPhoneByPhone (string phone);
    };
};

#endif 