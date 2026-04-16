function payNow() {

    fetch('/create_order/10')   // 🔥 change later dynamic
    .then(response => response.json())
    .then(data => {

        var options = {
           //k1
            "amount": data.amount,
            "currency": "INR",
            "name": "Rentify",
            "description": "Rental Payment",
            "order_id": data.id,

            "handler": function (response) {

                var form = document.createElement("form");
                form.method = "POST";
                form.action = "/verify_payment";

                for (var key in response) {
                    var input = document.createElement("input");
                    input.type = "hidden";
                    input.name = key;
                    input.value = response[key];
                    form.appendChild(input);
                }

                document.body.appendChild(form);
                form.submit();
            }
        };

        var rzp = new Razorpay(options);
        rzp.open();
    });
}