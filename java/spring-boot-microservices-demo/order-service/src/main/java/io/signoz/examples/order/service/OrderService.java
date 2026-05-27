package io.signoz.examples.order.service;

import io.opentelemetry.instrumentation.annotations.WithSpan;
import io.signoz.examples.order.model.Order;
import io.signoz.examples.order.model.OrderResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.server.ResponseStatusException;

import java.util.UUID;

@Service
public class OrderService {

    private final RestClient restClient;
    private final String inventoryServiceUrl;

    public OrderService(RestClient restClient, @Value("${inventory.service.url}") String inventoryServiceUrl) {
        this.restClient = restClient;
        this.inventoryServiceUrl = inventoryServiceUrl;
    }

    @WithSpan("order.process")
    public OrderResponse processOrder(Order order) {
        String url = inventoryServiceUrl + "/inventory/" + order.getProductId();
        
        try {
            InventoryItemDTO item = restClient.get()
                    .uri(url)
                    .retrieve()
                    .body(InventoryItemDTO.class);

            if (item != null && item.inStock()) {
                return new OrderResponse(
                        UUID.randomUUID().toString(),
                        order.getProductId(),
                        order.getQuantity(),
                        "SUCCESS",
                        item.productName()
                );
            } else {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Product out of stock");
            }
        } catch (RestClientResponseException e) {
            if (e.getStatusCode().isSameCodeAs(HttpStatus.NOT_FOUND)) {
                throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Product not found");
            }
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Inventory service unavailable", e);
        } catch (ResourceAccessException e) {
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Inventory service down", e);
        }
    }

    // DTO to map the response from inventory-service
    public record InventoryItemDTO(String productId, String productName, int availableStock, boolean inStock) {}
}
