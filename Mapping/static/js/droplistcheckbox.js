/**
 * jQuery.fn.dropdownCheckList(data);
 * example:
 * 		$('input').dropdownCheckList(['电话', '邮件', '地址']);
 */
(function($) {
	$.fn.dropdownCheckList = function(data) {
		var self = this;

		var container, options;

		this.each(function(k) {
			var _this = $(this),
				_options, _checkboxs;

			_this.wrap('<div class="control"></div>');
			_options = _this
				.parent()
				.wrap('<div class="select-chexkbox"></div>')
				.after('<ul class="options"></ul>')
				.next();

			$.each(data, function(i, n) {
				// _options.append('<li><input type="checkbox"><label>' + n + '</label></li>');
				var flag = 'c' + self.selector + Math.random() + k + i;
				_options.append('<li><label for="' + flag + '"><input type="checkbox" id="' + flag + '">'
					+ '<span>' + n + '</span></label></li>');
			});

			_this.on('click', function() {
				$('.select-chexkbox .options').not(_options).hide();
				_options.toggle();
			});

			_checkboxs = $('input', _options);
			_checkboxs.on('click', function(e) {
				//console.log(1);
				// e.stopPropagation();
				var str = ''
				_checkboxs.filter(':checked').each(function() {
					str += $(this).next().text() + ' | ';
				});
				str && (str = str.replace(/\s\|\s$/, ''));
				_this.val(str);
			});
/*			$('li', _options).on('click', function(e) {
				if (e.target.tagName.toLowerCase() !== 'input') {
					$(this).find('input').trigger('click');
				}
			});*/
		});
		container = $('.select-chexkbox'),
		options = $('.options', container);
		container.on('click', function(e) {
			e.stopPropagation();
		});
		$(document).on('click', function() {
			options.hide();
		});

		return this;
	};
})(jQuery);
