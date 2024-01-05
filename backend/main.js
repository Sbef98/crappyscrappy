// let's add a before save for the clas Node
Parse.Cloud.beforeSave("Node", function (request, response) {
    var node = request.object;
    // let's check if a node with same url already exists
    var query = new Parse.Query("Node");
    query.equalTo("url", node.get("url"));
    query.first({
        success: function (object) {
            if (object) {
                // if it exists, we return an error
                request.object.id = object.id;
                response.success();
            } else {
                // if it doesn't exist, we continue the save
                response.success();
            }
        },
        error: function (error) {
            response.error("Could not validate existence for this node object.");
        }
    });
    return request.object;
});