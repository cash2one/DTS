(function($) {

	$.fn.generalSelect = function(options){
		var empty = {};
		var defaults = {
			selectWidth : 80,
			selectBackground : "#7b6959",
			selectContent :[{"label" : "选择一","value" : "s1"}]
		}
		
		var settings = jQuery.extend(empty,defaults,options);
		
		//alert(JSON.stringify(settings))
		var B = settings;
		var flag = true;
		var obj = new Object();
			
		B.init = function(o){
				obj = o ;
				flag = B.verifySettings(B.selectWidth);
				if(!flag){return false ;}
				B.bindEvt()
		}
		B.verifySettings = function(width){
			width = parseInt(width);
			//alert(width)
			if(isNaN(width)){alert("您输入的selectWidth属性值有误！");return false ;}
			else{
				if(width < 80){B.selectWidth = 80;}
				else{B.selectWidth = width;}
				return true ;
			}
		}
		B.bindEvt = function(){
			B.addStyle();	
			B.addEvent();
		}
		B.addStyle = function(){
			var ss = "";
			var str1 = "<div class=\"general_select\" style=\"width:"+ (B.selectWidth+20) + "px\"><div class=\"general_select_div\"><div class=\"general_div_selected\" style=\"width:"+(B.selectWidth-10)+"px\">=请选择=</div><div class=\"general_img\" style=\"background-color:"+B.selectBackground+"\" ></div></div><ul class=\"general_select_ul\"  style=\"display: none;\">";
		 	//var str3 = "<li class=\"select_add_li\"><span class=\"sp1\">+1</span><span class=\"sp2\">显示全部</span></li></ul><input type=\"hidden\" name=\""+this.selectId+"\" value=\"\" class=\"general_select_input\"/></div>";
		 	//var str4 = "</ul><input type=\"hidden\" name=\""+obj.attr("id")+"\" value=\"\" /></div>";
		 	var str4 = "</ul><input type=\"hidden\" name=\"generalSelect\" value=\"\" /></div>";
		 	
		 	for(var i = 0;i < B.selectContent.length;i++)
	 		{
	 			var gs = B.selectContent[i];
	 			//alert(gs.hasOwnProperty("children"))
	 			
	 			if(gs.hasOwnProperty("children"))
	 			{
	 				ss += "<li class=\"select_normal select_li_one\"><span class=\"general_select_text\" style=\"width:"+(B.selectWidth-5)+"px\">"+gs.label+"</span><span class=\"add\">+</span></li>";
	 				for(var j = 0 ;j < gs.children.length;j++)
	 				{
	 					ss += "<li data-val=\""+(gs.children[j].value || "")+"\" class=\"select_normal select_li_two\"><span class=\"general_select_text2\" style=\"width:"+(B.selectWidth-15)+"px\">"+gs.children[j].label+"</span></li>";
	 				}
	 			}
	 			else{ss += "<li data-val=\""+gs.value+"\" class=\"select_normal select_li_three\"><span class=\"general_select_text\" style=\"width:"+(B.selectWidth-5)+"px\">"+gs.label+"</li>";}
	 		}
	 		
		 	obj.html(str1+ss+str4);
		}
		B.addEvent = function(){
			
			//alert(id)
			
			$(obj).find(".general_select").mouseover(function(e){
				
				//alert($(this).parent().attr("id"))
				$(this).find("ul").css("display","block");
				
			})
			$(obj).find(".general_select").mouseleave(function(event){
				//alert($(".general_select_ul").css("display"))
				$(this).find("ul").css("display","none");
				//alert("s")
				$(this).find(".select_li_two").css("display","none")
				$(this).find(".add").html("+");
				//num = 0;
			})
			
			
			$(obj).find(".select_normal").mouseover(function(){
				$(this).css("background",B.selectBackground);
				$(this).find(".add").css("color","white")
				//alert(Object.prototype.toString.call(this))
				
				
			});
			$(obj).find(".select_normal").mouseout(function(){
				$(this).css("background","");
				$(this).find(".add").css("color","#7b6959")
			});
			
			$(obj).find(".select_li_two,.select_li_three").click(function(event){
				$(this).parents(".general_select").find(".general_div_selected").html($(this).find("span").eq(0).html());
				//alert($(this).next())
				$(this).parent().css("display","none");
				$(this).parents(".general_select").find("input").val($(this).attr("data-val"))
				//alert($(this).attr("data-val"))
			});
			
			
			$(obj).find(".select_li_one").click(function(e){
				//alert("s")
				var flag = $(this).find(".add").html();
				
				if(flag == "+")
				{
					$(this).find(".add").html("-");
					B.opLi($(this),"show");
					  

				}
				if(flag == "-"){
					$(this).find(".add").html("+");
					B.opLi($(this),"hide");
				}
				//return false;
				
			});
			
		}
		B.opLi = function(data,op){
			if(op == "show"){op = "block";}
			if(op == "hide"){op = "none";}
			while(true)
			{
				if(data.next().hasClass("select_li_two"))
				{
					data.next().css("display",op);
					data = data.next();
				}
				else{break;}
			}
		}	
		//B.init();
		
		
		this.each(function(){
			//console.log(this)
			B.init($(this));

		});
		
		
		//console.log(this)
		
		return this;
		
	}
	/*
	 $(".hd").generalSelect({
				selectWidth : 160,
				selectBackground : "red",
				selectContent : [
					{
						"label" : "主菜单一",
						"value" : "ms1",
						"children" : [{"label":"阿斯顿","value":"ss1"},{"label":"啥时","value":"ss2"},{"label":"网上订购","value":"ss3"}]
					},
					{
						"label" : "主菜单二",
						"value" : "ms2"
					}
				]
			})
	 */

})(jQuery);