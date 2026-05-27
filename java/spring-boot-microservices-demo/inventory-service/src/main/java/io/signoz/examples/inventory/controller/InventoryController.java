package io.signoz.examples.inventory.controller;

import io.signoz.examples.inventory.model.InventoryItem;
import io.signoz.examples.inventory.service.InventoryService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
public class InventoryController {

    private final InventoryService inventoryService;

    public InventoryController(InventoryService inventoryService) {
        this.inventoryService = inventoryService;
    }

    @GetMapping("/inventory/{productId}")
    public InventoryItem getInventory(@PathVariable String productId) {
        InventoryItem item = inventoryService.checkInventory(productId);
        if (item == null) {
            // Simple error handling via ResponseStatusException
            throw new ResponseStatusException(
                HttpStatus.NOT_FOUND, "Product not found: " + productId
            );
        }
        return item;
    }
}
