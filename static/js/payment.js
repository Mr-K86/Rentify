function payNow() {

    fetch('/create_order/1')
    .then(response => response.json())
    .then(data => {

        var options = {
            // 🔥 IMPORTANT: test OR live consistent रखो
            "key": "rzp_live_SeE0JX90xaFfzU",   // या rzp_live_xxx (but same mode everywhere)
            "amount": data.amount,
            "currency": "INR",
            "name": "Rentify",
            "description": "Rental Payment",
            "order_id": data.id,

            // ❌ UPI force मत करो — Razorpay handle करेगा automatically
            // "method": "upi",

            "handler": function (response) {

                fetch('/verify_payment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(response)
                })
                .then(res => res.json())
                .then(result => {
                    alert("Payment Success!");
                    console.log(result);
                });

            },

            "theme": {
                "color": "#3399cc"
            }
        };

        var rzp = new Razorpay(options);
        rzp.open();
    });
}