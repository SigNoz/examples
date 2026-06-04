package io.signoz.examples.order.model;

public class OrderResponse {
    private String orderId;
    private String productId;
    private int quantity;
    private String status;
    private String productName;

    public OrderResponse() {}

    public OrderResponse(String orderId, String productId, int quantity, String status, String productName) {
        this.orderId = orderId;
        this.productId = productId;
        this.quantity = quantity;
        this.status = status;
        this.productName = productName;
    }

    public String getOrderId() { return orderId; }
    public void setOrderId(String orderId) { this.orderId = orderId; }

    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }

    public int getQuantity() { return quantity; }
    public void setQuantity(int quantity) { this.quantity = quantity; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }
}
