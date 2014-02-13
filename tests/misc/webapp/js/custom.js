function sidebar()
{
	$( ".arrow-sidebar" ).click(function() {
		if($(".arrow-sidebar").hasClass("hide-sidebar"))
		{
			//ocultar sidebar
			$( "#sidebar" ).animate(
			{
				width: "80px"
			  }, 
			  {
				duration: 1000,
				step: function( currentwidth ){
					$(".mainbar").css("padding-left", currentwidth);;
				},
				complete: function( currentwidth ){
					$(".arrow-sidebar").removeClass("hide-sidebar").addClass("show-sidebar");
					$( "#sidebar" ).addClass("mini");
				},
			  }
			)
		}else{
			//mostrar sidebar
			$( "#sidebar" ).animate(
			{
				width: "230px"
			  }, 
			  {
				duration: 1000,
				step: function( currentwidth ){
					$(".mainbar").css("padding-left", currentwidth);;
				},
				complete: function( currentwidth ){
					$(".arrow-sidebar").removeClass("show-sidebar").addClass("hide-sidebar");
					$( "#sidebar" ).removeClass("mini");
				},
			  }
			)
		}
	
	 
	  });
}

/* Navigation */

$(document).ready(function(){
	
	sidebar();


 
  $("#nav > li > a").on('click',function(e){
      if($(this).parent().hasClass("has_sub")) {
        e.preventDefault();
      }   

      if(!$(this).hasClass("subdrop")) {
        // hide any open menus and remove all other classes
        $("#nav li ul").slideUp(350);
        $("#nav li a").removeClass("subdrop");
        
        // open our new menu and add the open class
        $(this).next("ul").slideDown(350);
        $(this).addClass("subdrop");
      }
      
      else if($(this).hasClass("subdrop")) {
        $(this).removeClass("subdrop");
        $(this).next("ul").slideUp(350);
      } 
      
  });
});

$(document).ready(function(){
  $(".sidebar-dropdown a").on('click',function(e){
      e.preventDefault();

      if(!$(this).hasClass("open")) {
        // hide any open menus and remove all other classes
        $(".sidebar #nav").slideUp(350);
        $(".sidebar-dropdown a").removeClass("open");
        
        // open our new menu and add the open class
        $(".sidebar #nav").slideDown(350);
        $(this).addClass("open");
      }
      
      else if($(this).hasClass("open")) {
        $(this).removeClass("open");
        $(".sidebar #nav").slideUp(350);
      }
  });

});



/* Scroll to Top */

$(document).ready(function(){
  $(".totop").hide();

  $(function(){
    $(window).scroll(function(){
      if ($(this).scrollTop()>600)
      {
        $('.totop').slideDown();
      } 
      else
      {
        $('.totop').slideUp();
      }
    });

    $('.totop a').click(function (e) {
      e.preventDefault();
      $('body,html').animate({scrollTop: 0}, 500);
    });

  });
});
