window.HomeView = Backbone.View.extend({
	tagName: 'div',
    className: '',
    initialize: function () {
        this.render();
    },

    render: function () {
        $(this.el).html(this.template());
		$(this.el).i18n();
        return this;
    }

});