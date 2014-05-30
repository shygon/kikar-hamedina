$(document).ready(function () {
	$(".add-tag-button").click(function () {
		id = $(this).parent().data("statusid")
		tag = $(this).parent().find(".add-tag-input").val()
		$(this).parent().find(".add-tag-input").val("")

		url = "/add_tag_to_status/?id="+id+"&tag_str="+tag

		$.ajax({
			url: url,
			contentType: "application/json",
			success: function (data) {
				console.log("GOT RESPONSE")
				if (data['success']) {
					tag = data['tag']
					var source 		= $("#add-tag-to-status-template").html()
					var template 	= Handlebars.compile(source);
					var html    	= template(tag);
					$("#" + data['id'] + "-tags").prev().css("display","inline")
					$("#" + data['id'] + "-tags").append(html)
				}
				else {
					console.log(data)
					console.log("ERROR AT SERVER")
				}
			},
			error: function(data) {
				console.log("BADDDDD ERROR!!")
			}
		});
	});
})
