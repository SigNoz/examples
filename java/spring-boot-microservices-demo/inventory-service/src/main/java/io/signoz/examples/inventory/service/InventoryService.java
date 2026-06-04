package io.signoz.examples.inventory.service;

import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import io.signoz.examples.inventory.model.InventoryItem;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class InventoryService {

    private final Map<String, InventoryItem> inventoryMap;

    public InventoryService() {
        inventoryMap = new HashMap<>();
        // Hardcode 3-4 products as requested
        inventoryMap.put("P001", new InventoryItem("P001", "Laptop", 10));
        inventoryMap.put("P002", new InventoryItem("P002", "Smartphone", 0));
        inventoryMap.put("P003", new InventoryItem("P003", "Headphones", 50));
        inventoryMap.put("P004", new InventoryItem("P004", "Monitor", 5));
    }

    // Manual span creation using OpenTelemetry annotation
    @WithSpan("inventory.check")
    public InventoryItem checkInventory(@SpanAttribute("product.id") String productId) {
        return inventoryMap.get(productId);
    }
}
