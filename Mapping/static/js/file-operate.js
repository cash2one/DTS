/**
 * Created by yu on 6/24/14.
 */

String.prototype.replaceAll = stringReplaceAll;

function stringReplaceAll(AFindText,ARepText){
    raRegExp = new RegExp(AFindText,"g");
    return this.replace(raRegExp,ARepText)
}

//显示内容,标注
function showfilecont(fileid, url){
    $('#myModal').modal({
        backdrop:'static'
    });

    $('#myModal').on('show', function () {
        $("body").css({overflow:"hidden"});
    });

    $('#myModal').modal('show');
    $.getJSON(url,{fileid:fileid},function(result){
        var content=
            "<table class=\"table table-hover\">"+
              "<thead>"+
                "<tr>"+
                  "<th></th><th></th>"+
                "</tr>"+
              "</thead>"+
              "<tbody>";
            $.each(result,
                   function(i,value){
                        content +=
                        "<tr>"+
                          "<td id=\"line_"+i+"\">"+value+"</td>"+
                          "<td><input type=\"checkbox\" name=\"choosedlines\" value=\"line_"+i+"\""+(i==0?"checked":"")+" onclick=\"setskip()\"></td>"+
                        "</tr>";
                   }
            );
            content += "</tbody></table>"
            $("#trace2").html(content);
        });
    $('#header').val(fileid);
    $("#start_tag").show();
    $("#start_tag_p").show();
    $('#save_tag').hide();
    $('#pick_file').hide();
}


//开始标注,获取条数
function start(splitor,quoter,model_type) {
    $("#save_tag").show();
    $("#pick_file").show();
    $("#start_tag").hide();
    $("#start_tag_p").hide();
    $("#save_tag").removeClass("disabled");
    $("#pick_file").removeClass("disabled");
    var lines=new Array();
    $("input[name='choosedlines']:checkbox").each(function(){
        if($(this).is(":checked")){
            lines.push($('#'+$(this).val()).html().replaceAll(quoter,''))
        }
    });
    tmpfields = lines[0].split(splitor)
    var rs = new Array2DVar(tmpfields.length,lines.length)
    for (var i = 0; i < lines.length; i++){
        fields = lines[i].split(splitor)
        for (var j = 0; j < fields.length; j++){
            rs[j][i] = fields[j];
        }
    }
    var content=
        "<table id=\"cont\" class=\"table table-bordered table-striped\">"+
            "<thead>"+
            "</thead>"+
            "<tbody>";
    for(var i = 0; i < rs.length; i++){
        content +="<tr>"
        for(var j = 0; j < rs[i].length; j++){
            content +="<td>"+rs[i][j]+"</td>";
        }
        if(model_type == 'mapping'){
            //content +="<td><input type=\"text\" style=\"margin-bottom: 0px;\" name=\"field\" id=\"field_"+i+"\">"
            content += "<td><div id=\"field_"+i+"\"></div>";
        } else if (model_type == 'pick_file'){
            content +="<td><input type=\"checkbox\" style=\"margin-bottom: 0px;\" name=\"field\" id=\"field_"+i+"\">";
        } else if (model_type == 'pick'){
            //content +="<td><input type=\"text\" style=\"margin-bottom: 0px;\" name=\"field\" id=\"field_"+i+"\">"
            content += "<td><div id=\"field_"+i+"\"></div>";
        }
        content +="</td></tr>";
    }
    content += "</tbody></table>"
    $("#trace2").html(content);


    if(model_type == 'mapping'){
        for(var i = 0; i < rs.length; i++){
                $('#field_' + i).generalSelect({
                selectWidth : 160,
                selectBackground : "blue",
                selectContent : [
                     {"label":"客户数据编号","value":"cus_num"},{"label":"身份证号","value":"id"},{"label":"手机号", "value": "cell"},{"label":"电子邮箱", "value": "email"},{"label":"QQ号","value":"qq_num"},{"label":"姓名", "value": "name"},
                     {"label":"家庭住址", "value": "home_addr"},{"label":"家庭座机", "value": "home_tel"},{"label":"公司地址", "value": "biz_addr"},{"label":"公司座机", "value": "biz_tel"},
                    {"label":"其他地址", "value": "other_addr"},{"label":"银行卡号1", "value": "bank_card1"},{"label":"银行卡号2", "value": "bank_card2"},{"label":"客户的好坏标识", "value": "flag1"}
                    ,{"label":"客户的好坏标识1", "value": "flag2"},{"label":"标准客户状态", "value": "flag"},{"label":"逾期天数", "value": "def_days"},
                    {"label":"逾期期数", "value": "def_times"},{"label":"贷款金额范围", "value": "amount"},{"label":"数据注释", "value": "notes"},{"label":"申请日期", "value": "apply_date"},{"label":"数据观测日期", "value": "observe_date"},
		            {"label":"客户apicode", "value": "custApiCode"},{"label":"护照号码","value":"passport_number"},
                    {
                        "label":"贷款信息", "value": "loan_info",
                        "children":[{"label":"渠道","value":"apply_channel"},{"label":"贷款申请号","value":"apply_id"},{"label":"申请地址","value":"apply_addr"},{"label":"申请金额","value":"apply_amount"}
                        ,{"label":"申请产品","value":"apply_product"},{"label":"审批状态","value":"approval_status"},{"label":"批款时间","value":"approval_date"},{"label":"批款金额","value":"approval_amount"}
                        ,{"label":"抵押类型","value":"collateral"},{"label":"放款日期","value":"loan_date"},{"label":"贷款用途","value":"loan_purpose"},{"label":"贷款状态","value":"loan_status"}
                        ,{"label":"还款期数","value":"repayment_periods"}]
                    },
                    {
                        "label":"基本信息", "value": "basic_info",
                        "children":[{"label":"年龄","value":"age"},{"label":"民族","value":"race"},{"label":"性别","value":"gender"}
                        ,{"label":"生日","value":"birthday"},{"label":"婚姻状况","value":"marriage"},{"label":"教育背景","value":"edu"},{"label":"微信所属城市","value":"wechat_city"}
                        ,{"label":"微信昵称","value":"wechat_name"},{"label":"微信所属省份","value":"wechat_province"},{"label":"公积金缴纳情况","value":"providentfund"},{"label":"社保情况","value":"social_security"}
                        ,{"label":"身份证发证单位","value":"id_ps"},{"label":"身份证有效时间","value":"id_start"},{"label":"身份证失效时间","value":"id_end"},{"label":"身份证签发城市","value":"id_city"}
                        ,{"label":"证件类型","value":"id_type"},{"label":"户籍地址","value":"civic_addr"},{"label":"户籍状态","value":"civic_status"},{"label":"邮编","value":"postalcode"}
                        ,{"label":"城市","value":"city"},{"label":"省份","value":"province"}]
                    },
                    {
                        "label":"联系人信息", "value": "contact_info",
                        "children":[{"label":"联系人１姓名","value":"contact_name_1"},{"label":"联系人１关系","value":"contact_relation_1"},{"label":"联系人１手机号","value":"contact_cell_1"}
                        ,{"label":"联系人２姓名","value":"contact_name_2"},{"label":"联系人２关系","value":"contact_relation_2"},{"label":"联系人２手机号","value":"contact_cell_2"}
                        ,{"label":"联系人３姓名","value":"contact_name_3"},{"label":"联系人３关系","value":"contact_relation_3"},{"label":"联系人３手机号","value":"contact_cell_3"}
                        ,{"label":"联系人4姓名","value":"contact_name_4"},{"label":"联系人4关系","value":"contact_relation_4"},{"label":"联系人4手机号","value":"contact_cell_4"}
                        ,{"label":"联系人5姓名","value":"contact_name_5"},{"label":"联系人5关系","value":"contact_relation_5"},{"label":"联系人5手机号","value":"contact_cell_5"}]
                    },
                    {
                        "label":"资产，工作信息", "value": "worth_info",
                        "children":[{"label":"是否有房","value":"if_house"},{"label":"是否有车","value":"if_vehicle"},{"label":"房屋种类","value":"housing_cate"}
                        ,{"label":"车牌号","value":"vehicle_id"},{"label":"号牌种类","value":"type_vehicle_id"},{"label":"车类型","value":"vehicle_type"},{"label":"车架号","value":"car_code"},{"label":"发动机号","value":"driver_number"},{"label":"公司名称","value":"biz_name"}
                        ,{"label":"公司规模","value":"biz_size"},{"label":"行业","value":"industry"},{"label":"企业注册号", "value": 'reg_num'},{"label":"组织机构代码", "value": 'org_num'}
                        ,{"label": "公司类别", "value": "company_cate"},{"label":"月薪","value":"salary"},{"label":"职位","value":"position"},{"label":"工作年限","value":"working_period"}]
                    },
                    {
                        "label":"银行卡信息（失联", "value": "credit_info",
                        "children":[{"label":"银行卡开户日期","value":"acc_open_date"},{"label":"卡等级","value":"card_level"},{"label":"分行","value":"branch"}
                        ,{"label":"币种","value":"currency"},{"label":"剩余本金（失联）","value":"ins_balance"},{"label":"最新查询显示余额","value":"update_balance"}
                        ,{"label":"最新查询显示本金","value":"updaet_capital"},{"label":"最新查询显示日期","value":"update_date"},{"label":"最新查询显示滞纳金","value":"update_overduepayment"}
                        ,{"label":"最新查询显示利息","value":"update_interest"},{"label":"最新查询显示超限费","value":"update_overlimitfee"},{"label":"最新查询显示服务费","value":"update_servicefee"}
                        ,{"label":"账单日","value":"bill_day"},{"label":"账单邮编","value":"bill_post"},{"label":"账单地址","value":"bill_addr"}]
                    },
                    {
                        "label":"保险信息", "value": "ins_info",
                        "children":[{"label":"理赔金额","value":"ins_amount"},{"label":"理赔日期","value":"ins_date_claims"},{"label":"初登日期","value":"ins_firstlogindate"}
                        ,{"label":"新车价格","value":"ins_newvehicleprice"},{"label":"投保年限","value":"ins_period"}
                        ,{"label":"年均理赔次数","value":"ins_yearly_claims_num"}]
                    },
                    {
                        "label":"其他信息", "value": "oth_info",
                        "children":[{"label":"IMEI号","value":"imei"},{"label":"IMSI","value":"imsi"},{"label":"手机类型","value":"mobile_type"},{"label":"事件类型","value":"envent"},{"label":"设备请求标识","value":"af_swift_number"}
                        ,{"label":"申请渠道类型","value":"apply_type"},{"label":"设备标识字段类型","value":"device_type"},{"label":"设备标识","value":"device_id"}
                        ,{"label":"GID","value":"gid"},{"label":"其他变量１","value":"other_var1"},{"label":"其他变量1解释","value":"var_exp1"},{"label":"其他变量２","value":"other_var2"}
                        ,{"label":"其他变量2解释","value":"var_exp2"},{"label":"其他变量３","value":"other_var3"},{"label":"其他变量3解释","value":"var_exp3"}
                        ,{"label":"其他变量4","value":"other_var4"},{"label":"其他变量4解释","value":"var_exp4"}
                        ,{"label":"其他变量5","value":"other_var5"},{"label":"其他变量5解释","value":"var_exp5"}]
                    },
                ]
            })
        }
    }
    else if(model_type == 'pick_file'){
    }
    else if(model_type == 'pick'){
        for(var i = 0; i < rs.length; i++){
                $('#field_' + i).generalSelect({
                selectWidth : 160,
                selectBackground : "blue",
                selectContent : [
                    {"label":"身份证","value":"id"},{"label":"手机号","value":"cell"},{"label":"邮箱","value":"email"}
                ]
            })
        }
    }
}


function Array2DVar(x,y)
{
    this.length = x
    this.x = x
    this.y = y
    for(var i = 0; i < this.length; i++)
    this[i] = new Array(y)
}

function setskip(){
    var lines=new Array()
    var cc1 = $("input[name='choosedlines']:checkbox").each(function(){
        if($(this).is(":checked")){
            lines.push(parseInt($(this).val().split("_")[1]))
        }
    });
    lines.push(parseInt(2))
    lines.push(parseInt(3))
    lines.push(parseInt(5))
    $('#skip').val(lines[0]+1);
}

function shutdown(){
    url = '/als/analyst/shutdown/';
    var info = confirm('确定取消匹配吗?');
    if (info) {
        $.getJSON(url,{},function(result){
            if(result['msg'] == 0){
                alert('任务取消失败,请与管理原联系!');
            }
            location.reload();
        });
    };
}

//保存标注
function savetag(splitor,skip, tp){
    $("#save_tag").addClass("disabled");
    var field="";
    var header = $("#header").val();

    if (isNaN(skip)){
        alert("请输入整数!");
        return;
    }

    $("input[name='generalSelect']").each(function(){
        field += $(this).val()+","
    });

    if(tp ==1){
        url = "/als/manage/save_source_tag/";
    }
    else if(tp == 2)
        url = '/als/datatrans/save_tag/';
    $.get(url,{field:field.substr(0,field.length-1),header:header,splitor:splitor,skip:skip,},function(result){
        alert(result.msg);
        $('#myModal').modal('hide');
        $("body").css({overflow:"auto"});
        location.reload();
    });
}

//X关闭
function modalx(){
    $("body").css({overflow:"auto"});
}

//Close关闭
function modalc(){
    $("body").css({overflow:"auto"});
}

//保存标注
function pick_file(splitor,skip){
    $("#pick_file").addClass("disabled");
    var field="";
    var header = $("#header").val();

    if (isNaN(skip)){
        alert("请输入整数!");
        return;
    }

    $("input[name='field']:checkbox").each(function(){
        if(this.checked == true){
        field += 'check,';
        } else {
        field += ' ,';
        }
    });

    window.location='/als/datatrans/pick_file/?fileid=' + header +'&columns=' + field + '&splitor=' + splitor;
}

function distribute(fileid){
    $('#Dist').modal({
        backdrop:'static'
    });

    $('#Dist').on('show', function () {
        $("body").css({overflow:"hidden"});
    });
    $('#Dist').modal('show');

    $("#selectpicker").find("option").remove().end();
    $.getJSON('/als/datatrans/get_sourcefiles/',{fileid:fileid},function(result){
        for(key in result){
        $('#selectpicker').append($('<option></option>')
                                 .attr('value',key)
                                 .text(result[key])
                                );
        }
    });
    $('#header2').val(fileid);
}

function start_distribute(fileid){
    var fileids="";
    var header = $("#header2").val();
    $("#selectpicker option:selected").each(function(){
        fileids += $(this).val() + ",";
    });
    $.get("/als/datatrans/start_distribute/",{fileids:fileids.substr(0,fileids.length-1),fileid:header},function(result){
        alert(result);
    });
}


function show_confirm(self){
    $("#confirm_fileid").val($(self).val());
    $("#confirm_modal").modal('show');
}

function start_mapping(){
    $('#confirm_modal').modal('hide');
    var fileid = $("#confirm_fileid").val();
    var select = $("#select-task").val();
    if (select == 'xdhx3') {
        $("#confirm_fileid2").val(fileid);
        $("#confirm_select").val(select);
        $("#select_xd3_modal").modal('show');
    }else if(select == 'ltst|ltid|dxst|dxid'){
        $("#confirm_fileid2").val(fileid);
        $("#confirm_select").val(select);
        $("#select_operator_modal").modal('show');
    }else if(select == 'tyhx3'){
        $("#confirm_fileid2").val(fileid);
        $("#confirm_select").val(select);
        $("#select_hx3_modal").modal('show');
    }else if(select == 'bcjq'){
        $("#confirm_fileid2").val(fileid);
        $("#confirm_select").val(select);
        $("#select_bcjq_modal").modal('show');
   }else if(select == 'loss'){
       $("#confirm_fileid2").val(fileid);
       $("#confirm_select").val(select);
       $("#select_loss_modal").modal("show");
    }else{
        url = '/als/analyst/start_mapping/';
        $.getJSON(url,{fileid:fileid, select:select},function(result){
            $("#confirm_fileid").val('');
            alert(result['msg']);
            location.reload();
        });
    };
}

function loss_submit(){
    $("#select_loss_modal").modal("hide");

    var fileid  = $("#confirm_fileid2").val();
    var select = $("#confirm_select").val();
    var data = $('#loss_data').is(':checked');
    var mark = $('#loss_mark').is(":checked");
    var collect = $('#loss_collect').is(':checked');
    var code = $('#loss_code').val();
    if (code == ""){
    alert("授权码不能为空");
    }else{
        url = '/als/analyst/loss_model/';
        $.getJSON(url,{fileid:fileid, select:select, loss_data: data, loss_mark: mark, loss_collect:collect, loss_code:code},function(result){
           $("#confirm_fileid").val('');
           alert(result['msg']);
           location.reload();
        });
    }
}


function operator_submit(){
    $("#select_operator_modal").modal("hide");
    var fileid  = $("#confirm_fileid2").val();
    var select = $("#confirm_select").val();
    var lt_cell_state = $('#lt_cell_state').is(':checked');
    var lt_card_name = $('#lt_card_name').is(':checked');
    var dx_cell_state = $('#dx_cell_state').is(':checked');
    var dx_card_name = $('#dx_card_name').is(':checked');
    url = '/als/analyst/operator_model/';
    $.getJSON(url,{fileid:fileid, select:select,lt_cell_state: lt_cell_state, lt_card_name: lt_card_name, dx_cell_state: dx_cell_state, dx_card_name:dx_card_name},function(result){
        $("#confirm_fileid").val('');
        alert(result['msg']);
        location.reload();
    });
}

function bcjq_submit(){
    $("#select_bcjq_modal").modal("hide");
    var fileid  = $("#confirm_fileid2").val();
    var select = $("#confirm_select").val();
    var bcjq_card_name = $('#bcjq_card_name').is(':checked');
    var bcjq_card_cell = $('#bcjq_card_cell').is(':checked');
    var bcjq_card_name_id = $('#bcjq_card_name_id').is(':checked');
    var bcjq_name_id_cell = $('#bcjq_name_id_cell').is(':checked');
    url = '/als/analyst/bcjq_model/';
    $.getJSON(url,{fileid:fileid, select:select,bcjq_card_name: bcjq_card_name, bcjq_card_cell: bcjq_card_cell, bcjq_card_name_id: bcjq_card_name_id, bcjq_name_id_cell:bcjq_name_id_cell},function(result){
        $("#confirm_fileid").val('');
        alert(result['msg']);
        location.reload();
    });
}

function qy_submit(){
    $("#select_qy_modal").modal("hide");
    var fileid  = $("#confirm_fileid2").val();
    var select = $("#confirm_select").val();
    var name_company = $('#name_company').is(':checked');
    var card_company = $('#card_company').is(':checked');
    url = '/als/analyst/qy_model/';
    $.getJSON(url,{fileid: fileid, select: select, card_company: card_company, name_company: name_company},function(result){
        $("#confirm_fileid").val('');
        alert(result['msg']);
        location.reload();
    });
}

function submit(){
    $("#select_hx_modal").modal("hide");
    $("#select_xd_modal").modal("hide");
    $('#select_xd3_modal').modal("hide");
    $('#select_hx3_modal').modal("hide");
    var fileid  = $("#confirm_fileid2").val();
    var select = $("#confirm_select").val();
    if (select == 'xdhx3') {
        var sort = $("#xd3_sort").val();
        var sorts  = sort.split(',');
        var meals = '';
        for (var key in sorts) {
            //meals[key] = key;
             var sortt = $("#" + sorts[key]).is(':checked');
             if (sortt) {
                meals = meals + ',' + sorts[key];
             };
        };

    } else if (select == 'tyhx3'){
        var sort = $("#hx3_sort").val();
        var sorts  = sort.split(',');
        var meals = '';
        for (var key in sorts) {
            //meals[key] = key;
             var sortt = $("#" + sorts[key]).is(':checked');
             if (sortt) {
                meals = meals + ',' + sorts[key];
             };
        };
    } else{
        var apply = $("#apply").is(':checked');
        var behavior = $("#behavior").is(':checked');
        var special = $("#special").is(':checked');
        var account = $("#account").is(':checked');
    };
    url = "/als/analyst/get_select_model/";
    if (select == 'xdhx3'){
        $.getJSON(url,{fileid:fileid, select:select, meals:meals},function(result){ //apply:apply, location3: location3, stab: stab, special:special, cons:cons, media:media, account:account, paycon:paycon, score_br:score_br, score_cust: score_cust, telecheck: telecheck, monthaccount: monthaccount, scorebank: scorebank,scorep2p: scorep2p, scorecf: scorecf},function(result){
            $("#confirm_fileid").val('');
            alert(result['msg']);
            location.reload();
        });
    }else if (select == 'tyhx3'){
        $.getJSON(url,{fileid:fileid, select:select, meals:meals},function(result){//auth3: auth3, stab3: stab3, special3:special3, cons3:cons3, media3:media3, brand3: brand3, assets3: assets3, title3: title3},function(result){
            $("#confirm_fileid").val('');
            alert(result['msg']);
            location.reload();
        });
    }else{
    $.getJSON(url,{fileid:fileid, select:select, apply:apply, behavior: behavior, special:special, account:account,paycon:paycon,telecheck:telecheck,monthaccount:monthaccount},function(result){
        $("#confirm_fileid").val('');
        alert(result['msg']);
        location.reload();
    });
};
}

function shutdown(){
    url = '/als/analyst/shutdown/';
    var info = confirm('确定取消匹配吗?');
    if (info) {
        $.getJSON(url,{},function(result){
            if(result.msg == 0) {
            alert('fail pelease connect admin');
            };
            location.reload();
        })
    };
}

function delete_all(codeid){
    url = '/als/coder/delete_all/';
    var info = confirm('确定删除吗');
    if (info) {
        $.getJSON(url,{codeid:codeid},function(result){
            alert(result);
        });
    };
}

function delete_this(codeid){
    url = '/als/coder/delete_this/';
    var info = confirm('确定删除吗');
    if (info) {
        $.getJSON(url,{codeid:codeid},function(result){
            if (result.msg == 0){
                location.reload();
            }else{
                alert(result.msg);
            }
        });
    };
}

function to_user(codeid){
    url = '/als/coder/to_user/';
    var info = confirm('确定标注吗？');
    if (info) {
        $.getJSON(url,{codeid:codeid},function(result){
            if (result.msg == 0){
                location.reload();
            }else {
                alert(result.msg);
            }

        });
    };
}

function put_in_db(fileid){
    url = '/als/phone/put_in_db/';
    var info = confirm('确定进行筛选空号吗');
    if (info) {
        $.getJSON(url,{fileid:fileid},function(result){
            alert(result);
        });
    };
}


function get_results(fileid){
    url = '/als/phone/get_result/';
    if (true) {
        $.getJSON(url,{fileid:fileid},function(result){
            alert(result);
        });
    };
}

function mail_to_coder(){
    url = '/als/analyst/mail_to_coder/';
    var info = confirm("确定要获取授权码吗？")
    var fileid  = $("#confirm_fileid2").val();
    var select = $("#confirm_select").val();
    var data = $('#loss_data').is(':checked');
    var mark = $('#loss_mark').is(":checked");
    var collect = $('#loss_collect').is(':checked');
    if (info) {
        $.getJSON(url,{fileid: fileid, data:data, mark:mark, collect:collect},function(result){
            alert(result);
        });
    };
}

function send_mail(fileid){
    url = '/als/analyst/send_email/';
    var info = confirm('确定发送给客户吗')
    if (info) {
        $.getJSON(url,{fileid: fileid},function(result){
            alert(result);
        });
    };
}

function get_passwd(fileid){
    url = '/als/analyst/get_mappingfile_passwd/';
    $.getJSON(url,{fileid: fileid},function(result){
        alert(result);
    });
}

function let_get(fileid){
    url = '/als/analyst/let_cus_get/';
    var info = confirm('确定赋予客户查看的权限么')
    if (info) {
        $.getJSON(url,{fileid:fileid},function(result){
            alert(result);
        });
    };
}

function collect_date(fileid){
    url = '/als/analyst/to_collect/';
    var info = confirm('确定加入数据集市吗');
    if(info){
        $.getJSON(url,{fileid:fileid},function(result){
            if(result.msg) {alert(result.msg);}
            location.reload();
        });
    };
}


function del_meal(fileid){
    url = '/als/meal/delete_meal/';
    var info = confirm('确定删除吗');
    if(info){
        $.getJSON(url,{fileid:fileid},function(result){
            alert(result);
            window.location.href = '/als/meal/meal_list/'; 
        });
    };
}


$("#subbtn").click(function(){
             alert('正在抽样中，请稍后到文件列表查看');
             $.ajax({
                 type: "post",
                 url: "/als/analyst/make_file/",     
                 data: $("#myForm").serialize(),    
                 success: function(msg) {
                    if (msg.msg) {
                        alert(msg.msg);
                    };
                 },
                 error: function() {
                 }
             })
         });


$("#del_report").click(function(){
             var info = confirm('确定删除吗');
             var fileid = $("#del_report").val();
             var url2 = "/als/analyst/cus_report_files/?fileid=";
             if(info){
                 $.ajax({
                     type: "post",
                     url: "/als/analyst/delete_report/",     
                     data: {fileid: fileid},    
                     success: function(data) {
                        url2 = url2 + data.fileid
                        window.location.href = url2;
                     },
                     error: function(data) {
                        alert('删除失败');
                     }
                 })
             }
         });


$(function(){
    $("#custom_num").click(function() {
        var select = $('#custom_num option:selected').val();
        $.ajax({
            type: "GET",
            url:"/als/analyst/get_file_num/",
            data: {custom_num:select},
            success: function(msg){
                if (msg) {
                    $('#file_num').html('');
                    $("#file_num").append('<option value="请选择">请选择</option>');
                    for (var i = 0; i < msg.file_num.length; i++)
                        $('#file_num').append($('<option></option>')
                            .attr('value',msg.file_num[i])
                            .text(msg.file_num[i])
                            );}
                else {
                    alert('fail');
                    $('#file_num').html('');
                    $("#file_num").append('<option value="请选择">请选择</option>');}
            },
            error: function(){
                alert("获取文件编号出错！");
                }
            });
        });
    });



$(function(){
    $("#re_passwd").click(function(){
        var mail = $('#mail').val();
        var uname = $('#uname').val();
        $.ajax({
            type: "GET",
            url: "/accounts/verify/",
            data:{mail:mail, uname:uname},
            success:function(msg){
                if(msg.success){
                    $("#verfiy_num").html('msg.verfiy_num');
                    alert(msg.success);
                }else{
                    alert(msg.err);
                };
            },
            error: function(){
                alert("fail");
            }
        });

    });
});
