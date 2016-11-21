function delete_file(fileid,filename){
    url = '/als/custom/delete_files/';
    var confirm_info='确认删除测试文件：' + filename + '  吗？\n注意：删除后测试数据与匹配结果均无法恢复，请确认测试完成后再删除！';
    var info = confirm(confirm_info);
    if(info){
        $.getJSON(url,{fileid:fileid},function(result){
            alert(result);
            location.reload(location.href); 
        });
    };
}
