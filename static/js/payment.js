// payment.html में यह script tag add करो:
// <script>const ITEM_ID = {{ item_id }};</script>
// उसके बाद यह JS file load करो।

function payNow() {

    // ✅ FIX 1: /create_order/1 की जगह असली item_id use करो
    // पहले हमेशा ₹1 charge होता था — अब DB से सही price आएगी
    fetch('/create_order/' + ITEM_ID)
    .then(response => response.json())
    .then(data => {

        if (data.error) {
            alert("Error: " + data.error);
            return;
        }

        var options = {
            "key": "rzp_live_SeE0JX90xaFfzU",
            "amount": data.amount,        // paise में (backend से आया)
            "currency": "INR",
            "name": "Rentify",
            "description": "Rental Payment",
            "order_id": data.id,          // ✅ जरूरी है — Razorpay order ID

            "handler": function (response) {
                // ✅ FIX 2: पहले verify करो, तभी success दिखाओ
                // पहले alert पहले आता था — verify का result देखे बिना

                fetch('/verify_payment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        razorpay_payment_id: response.razorpay_payment_id,
                        razorpay_order_id:   response.razorpay_order_id,
                        razorpay_signature:  response.razorpay_signature
                    })
                })
                .then(res => res.json())
                .then(result => {
                    if (result.status === "success") {
                        // ✅ सिर्फ verify होने के बाद success दिखाओ
                        alert("✅ Payment Successful! Your rental is confirmed.");
                        window.location.href = "/my_rentals";
                    } else {
                        // ✅ FIX 3: Failure case handle करो
                        alert("❌ Payment verification failed: " + (result.message || "Unknown error"));
                    }
                })
                .catch(err => {
                    alert("❌ Network error during verification: " + err.message);
                });
            },

            // ✅ FIX 4: Payment failure भी handle करो
            "modal": {
                "ondismiss": function() {
                    console.log("Payment modal closed by user");
                }
            },

            "prefill": {
                "name": "",
                "email": "",
                "contact": ""
            },

            "theme": {
                "color": "#3399cc"
            }
        };

        var rzp = new Razorpay(options);

        rzp.on('payment.failed', function (response) {
            alert("❌ Payment Failed: " + response.error.description);
            console.error("Payment failed:", response.error);
        });

        rzp.open();
    })
    .catch(err => {
        alert("❌ Could not create order: " + err.message);
    });
}
