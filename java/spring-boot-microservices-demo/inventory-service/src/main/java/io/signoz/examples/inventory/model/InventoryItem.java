package io.signoz.examples.inventory.model;

public class InventoryItem {
    private String productId;
    private String productName;
    private int availableStock;
    private boolean inStock;

    public InventoryItem() {
    }

    public InventoryItem(String productId, String productName, int availableStock) {
        this.productId = productId;
        this.productName = productName;
        this.availableStock = availableStock;
        this.inStock = availableStock > 0;
    }

    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }

    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }

    public int getAvailableStock() { return availableStock; }
    public void setAvailableStock(int availableStock) { this.availableStock = availableStock; }

    public boolean isInStock() { return inStock; }
    public void setInStock(boolean inStock) { this.inStock = inStock; }
}
