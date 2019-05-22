$(document).ready(function () {
    var window = $("#modal-share"),
        undo = $(".undo")
                .on("click", function() {
                    window.kendoWindow({
                        modal: true,
                        visible: false,
                        content: {
                            url: $(this).data('url'),
                            dataType: "json",
                            template: "#= data.html #"
                        }
                    });
                    window.data("kendoWindow").center().open();
                });

    var onClose = function() {
        undo.show();
    };

    window.kendoWindow({
        width: "600px",
        height: "270px",
        title: "Share",
        actions: [
            "Minimize",
            "Maximize",
            "Close"
        ],
        close: onClose,
        modal: true,
        visible: false
    });
});
