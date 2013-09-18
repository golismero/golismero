window.SidebarView = Backbone.View.extend({
	 tagName: 'div',
    className: 'content-sidebar',
    initialize: function () {
        this.render();
    },

    render: function () {
        $(this.el).html(this.template());
		
        return this;
    },

    selectMenuItem: function (menuItem) {
        $('#nav li').removeClass('active');
        if (menuItem) {
            $('#nav li.' + menuItem).addClass('active');
        }
    }

});