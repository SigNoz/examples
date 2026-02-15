import { Injectable, NotFoundException } from '@nestjs/common';
import { Traced } from '../decorators/traced.decorator';

export interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

export interface CreateUserDto {
  name: string;
  email: string;
}

@Injectable()
export class UserService {
  private users: User[] = [
    {
      id: '1',
      name: 'John Doe',
      email: 'john.doe@example.com',
      createdAt: new Date('2023-01-01'),
    },
    {
      id: '2',
      name: 'Jane Smith',
      email: 'jane.smith@example.com',
      createdAt: new Date('2023-01-02'),
    },
  ];

  @Traced('user_creation')
  async createUser(userData: CreateUserDto): Promise<User> {
    // Simulate async operation
    await new Promise((resolve) => setTimeout(resolve, 100));

    const newUser: User = {
      id: Math.random().toString(36).substring(7),
      name: userData.name,
      email: userData.email,
      createdAt: new Date(),
    };

    this.users.push(newUser);
    return newUser;
  }

  @Traced() // Uses default name: UserService.findById
  async findById(id: string): Promise<User> {
    // Simulate async operation
    await new Promise((resolve) => setTimeout(resolve, 50));

    const user = this.users.find((u) => u.id === id);
    if (!user) {
      throw new NotFoundException(`User with ID ${id} not found`);
    }

    return user;
  }

  @Traced('get_all_users')
  async findAll(): Promise<User[]> {
    // Simulate async operation
    await new Promise((resolve) => setTimeout(resolve, 30));

    return this.users;
  }

  @Traced('user_search')
  async searchByEmail(email: string): Promise<User[]> {
    // Simulate database query delay
    await new Promise((resolve) => setTimeout(resolve, 75));

    return this.users.filter((user) =>
      user.email.toLowerCase().includes(email.toLowerCase()),
    );
  }
}
