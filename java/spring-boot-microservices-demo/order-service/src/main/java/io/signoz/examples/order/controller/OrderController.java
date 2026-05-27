package io.signoz.examples.order.controller;

import io.signoz.examples.order.model.Order;
import io.signoz.examples.order.model.OrderResponse;
import io.signoz.examples.order.service.OrderService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping("/orders")
    public OrderResponse createOrder(@RequestBody Order order) {
        return orderService.processOrder(order);
    }
}
