function payNow(item_id) {

    fetch(`/create_order/${item_id}`)
    .then(res => res.json())
    .then(order => {

        if (!order.id) {
            alert("Order creation failed");
            return;
        }

        var options = {
            key: "rzp_live_SeE0JX90xaFfzU",
            amount: order.amount,
            currency: order.currency,
            name: "Rentify",
            description: "Rental Payment",
            order_id: order.id,

            handler: function (response) {

                fetch('/verify_payment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(response)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "success") {
                        alert("Payment Successful");
                        window.location.href = "/my_rentals";
                    } else {
                        alert("Payment failed");
                    }
                });
            },

            theme: {
                color: "#3399cc"
            }
        };

        var rzp = new Razorpay(options);
        rzp.open();
    })
    .catch(err => {
        console.log(err);
        alert("Server error in order creation");
    });
}