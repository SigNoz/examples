import { Controller, Get, Post, Body, Param, Query } from '@nestjs/common';
import { UserService, User, CreateUserDto } from './user.service';

@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Post()
  async createUser(@Body() createUserDto: CreateUserDto): Promise<User> {
    return this.userService.createUser(createUserDto);
  }

  @Get()
  async findAll(): Promise<User[]> {
    return this.userService.findAll();
  }

  @Get('search')
  async searchByEmail(@Query('email') email: string): Promise<User[]> {
    return this.userService.searchByEmail(email);
  }

  @Get(':id')
  async findById(@Param('id') id: string): Promise<User> {
    return this.userService.findById(id);
  }
}
