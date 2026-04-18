
document.addEventListener("DOMContentLoaded", function () {

    console.log("DOM Loaded");

    const btn = document.getElementById("payBtn");

    if (!btn) {
        console.log("Button NOT found ❌");
        return;
    }

    console.log("Button found ✅");

    btn.addEventListener("click", function () {

        console.log("Button Clicked 🔥");

        const itemId = btn.getAttribute("data-item-id");

        fetch('/create_order/' + itemId)
        .then(res => res.json())
        .then(order => {

            var options = {
                "key": "rzp_live_SeE0JX90xaFfzU",
                "amount": order.amount,
                "currency": "INR",
                "name": "Rentify",
                "order_id": order.id,

                "handler": function (response){
                    alert("Payment Success");
                }
            };

            var rzp = new Razorpay(options);
            rzp.open();
        });

    });

});