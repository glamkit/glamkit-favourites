var DEBUG = true;

fav_management_links_binding = function(container){
    var fav_links;
    if (container){
        fav_links = container.find(".fav_link");
    }
    else {
        fav_links = $(".fav_link")
    }
    fav_links.each(function(i, val){
            favLinks.push(new favLink($(val)))
    });
    $(".favourites_links_container").hover(
        function(){
            $(this).find(".favourites_links").show();
        },
        function(){
            $(this).find(".favourites_links").hide();
        }
    );
    
};

// constructor
favLink = function(link){
    /*
    AJAXy adding/removing of items from the collection
    
    Workflow:
    x User clicks on the link
    x If the link is 'add to the new collection',
        user is redirected to the newly created page
    x For 'remove' & 'add' - the reply from the server will
        contain the new html for the favourites links 
    */
    
    var self = this;
    
    self.link = link;
    self.action_url = link.attr("href");
    self.favourites_links_container = self.link.parents().filter(".favourites_links_container");
    
    var onOK = function(){
        $.post(self.action_url, {"is_ajax": true}, 
            function(data){
                if (data.status !== "OK"){
                    return alert("Request failed");
                }
                if (data.action === "redirect"){
                    window.location.href = data.url;
                }
                else {
                    self.favourites_links_container.html(data.html);
                    fav_management_links_binding(self.favourites_links_container);
                }
            }, "json");
            
        return false;
    };  
    
    this.link.click(onOK);
    
};

// constructor
removeLink = function(link){
    // TODO - refactoring / inheritance - ?
    /*
    AJAXy removal of items from the collection on the 
    "collection_details" page
    
    Workflow:
    x User clicks "remove"
    x "Are you sure?" message appears
    x "Cancel" and "Submit" buttons appear
    x If user clicks "submit" ->
        - request is send, if everything is OK the item gets removed from the page
    x If user clicks "cancel" ->
        - message and submit buttons disappear
    */ 
    var self = this;
    
    self.link = link;
    self.action_url = link.attr("href");
    self.item_container = link.parents().filter(".item_container");
    self.container = link.parents().filter(".meta_container");
    self.are_you_sure_container = self.container.find(".are_you_sure");
    self.submit_buttons_container = self.container.find(".submit_buttons_remove");
    self.form = self.container.find("form");
    self.edit_bar = self.container.find(".edit_bar");
    self.cancel_button = self.submit_buttons_container.find(".cancel");
    
    self.showEditBar = function(){
        self.edit_bar.show();
    };
    
    self.hideEditBar = function(){
        self.edit_bar.hide();
    };
    
    self.removeSelf = function(){
        self.item_container.hide().remove();
    };
    
    self.showAreYouSure = function(){
        self.are_you_sure_container.show();
    };
    
    self.hideAreYouSure = function(){
        self.are_you_sure_container.hide();  
    };
    
    self.showSubmitButtons = function(){
        self.submit_buttons_container.show();
    };
    
    self.hideSubmitButtons = function(){
        self.submit_buttons_container.hide();
    };
    
    var onOK = function(){
        $.post(self.action_url, {"is_ajax": true}, 
            function(data){
                if (data.action === "redirect"){
                    return (window.location.href = data.url);
                }
                if (data.status === "OK"){
                    self.removeSelf();
                }
                else {
                    alert("Couldn't remove the item from favourites. Error occured");
                }
            },
            "json"
        );
        return false; 
    };
    
    var onCancel = function(){
        self.showEditBar();
        self.hideAreYouSure();
        self.hideSubmitButtons();
    };
    
    link.click(function(){
        self.hideEditBar();
        self.showAreYouSure();
        self.showSubmitButtons();
        self.form.submit(onOK);
        self.cancel_button.click(onCancel);
        return false;
    });
    
};

// constructor
fancyForm = function(form){
    /*
    Form on the "collection_details" page which allows AJAXy
    editing of the metadata for the collection page
    
    Workflow is:
    x When "edit" is pressed, div with the data will be replaced by the form
    x Buttons "submit" and "cancel" appear
    x If "submit" is pressed ->
        - if form contains no errors, submit buttons disappear, and form is replaced
            by the updated metadata fetched from the server
        - if form does contain errors, they are displayed above the form
    x If "cancel" is pressed ->
        - submit buttons and form is hidden
        - metadata reappears on the stage
    */
    var self = this;
    
    self.form = form;
    self.container = form.parents().filter(".meta_container");
    self.form_container = self.container.find(".form_container");
    
    self.action_url = form.attr("action");
    self.data_container = self.container.find(".details");
    self.submit_buttons_container = self.container.find(".submit_buttons_edit");
    self.edit_bar = self.container.find(".edit_bar");
    self.cancel_button = self.submit_buttons_container.find(".cancel");
    
    self.edit_button = self.container.find(".edit_button");
    
    self.showForm = function(data){
        self.form_container.html(data.form);
    };
    
    self.hideForm = function(){
        self.form_container.html("");
    };
    
    self.showEditBar = function(){
        self.edit_bar.show();
    };
    
    self.hideEditBar = function(){
        self.edit_bar.hide();
    };
    
    self.showSubmitButtons = function(){
        self.submit_buttons_container.show();
    };
    
    self.hideSubmitButtons = function(){
        self.submit_buttons_container.hide();
    };
    
    self.showData = function(){
        self.data_container.show();   
    };
    
    self.hideData = function(){
        self.data_container.hide();
    };
    
    self.updateData = function(data){
        self.hideForm();
        self.data_container.html(data.details);
    };
    
    var onEdit = function(data){
        self.hideData();
        self.hideEditBar();
        self.showForm(data);
       
        self.showSubmitButtons();
        self.form.submit(onOK);
        self.cancel_button.click(onCancel);
        return false;
    };
    
    var onOK = function(){
        $.post(self.action_url, $(this).formSerialize()+"&is_ajax=true", function(data){
            // change to normal view with the updated data
            if (data.action === "show_errors"){
                self.showForm(data);
            }
            else{
                self.updateData(data);
                self.showData();
                self.showEditBar();
                self.hideForm();
                self.hideSubmitButtons();
            }
        }, "json");
        return false;
    };
    
    var onCancel = function(){
        // reset to normal view
        self.hideForm();
        self.showEditBar();
        self.hideSubmitButtons();
        self.showData();
    };
    
    self.edit_button.click(function(){
        $.get(self.action_url, {"is_ajax": true}, onEdit, "json");
        return false;
    });   
};